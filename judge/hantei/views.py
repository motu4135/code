from django.shortcuts import render, redirect
from .models import AcquiredCredits, SubjectTable # SubjectTbaleを.formsからインポートしていたので修正(10/30/23)
from .forms import AcquiredSubjectForm

# Create your views here.

# 取得済み科目登録画面の処理を定義
def subject_list(request):
    selected_subjects = []
    
    # 修正時（取得済みの一時データがある場合）はsessionデータを保持
    if 'selected_subjects' in request.session:
        selected_subjects = request.session['selected_subjects']
    
    # データ取得時の処理    
    if request.method == 'POST':
        form = AcquiredSubjectForm(request.POST)
        if form.is_valid():
            selected_subjects = form.cleaned_data['subjects']
            # 選択された科目データをセッション情報として保持
            request.session['selected_subjects'] = [subject.id for subject in selected_subjects]
            return redirect('hantei:confirm_subjects')      
            
    else:
        form = AcquiredSubjectForm(initial={'subjects': SubjectTable.objects.filter(id__in=selected_subjects)})
    
    context = {'form': form}
    return render(request, 'subject_list.html', context)

# 確認画面の処理を定義
def confirm_subjects(request):
    if request.method == "POST":
        if 'action' in request.POST:
            if request.POST['action'] == "confirm":
                # 確定処理       
                if 'selected_subjects' in request.session:
                    subjects = SubjectTable.objects.filter(id__in=request.session['selected_subjects'])
                    # プロトタイプでは格納データは再利用しないので既存データを削除
                    AcquiredCredits.objects.all().delete()
                    # 科目を取得済み科目テーブルに登録
                    for subject in subjects:
                        AcquiredCredits(subject=subject).save()
                    # 確認のための一時データを削除
                    del request.session['selected_subjects']                   
                    return redirect('hantei:judgement') # 判定画面にリダイレクト
                
            elif request.POST['action'] == "back": # 戻るボタンの処理
                return redirect('hantei:subject_list')
                
    if 'selected_subjects' in request.session:
        subjects = SubjectTable.objects.filter(id__in=request.session['selected_subjects'])            
        return render(request, 'confirm_subjects.html', {'subjects': subjects})
    
    return redirect('hantei:subject_list') # セッションに科目がない場合は科目リストページに戻る


# 判定、結果表示のクラス・関数を定義(全学共通)
class JudgeCommon:
        
    # 区分1＝全学共通科目(必修)の判定
    def judge_cat1(self):
        # 全学共通科目(必修)を科目テーブル、取得済み科目テーブルにから取得(プロトタイプでは留学生科目を除外)
        all_required_subjects = SubjectTable.objects.filter(category1=1, foreign_student_flag=False)
        acquired_subjects_of_cat1 = AcquiredCredits.objects.filter(subject__category1=1)

        # 未取得科目のリスト化：必修科目は個別に科目をチェックする
        not_acquired_subjects_cat1 = set(all_required_subjects) - set([acq.subject for acq in acquired_subjects_of_cat1])
        
        # 区分1の合計取得単位数
        acquired_credits_cat1 = sum(acq.subject.credits for acq in acquired_subjects_of_cat1)
        
        required_cat1 = 0 # 不足単位数を記録する変数
        
        if acquired_credits_cat1 == 10:
            judge_flag1 = True # 各判定項目ごとに判定フラグに結果を代入
        else:
            judge_flag1 = False
            required_cat1 = 10 - acquired_credits_cat1 # 要件未達の場合は不足単位数を算出
               
        return not_acquired_subjects_cat1, acquired_credits_cat1, required_cat1, judge_flag1
       
    # 全学共通科目(選択必修)～学部基礎(情報)サブクラス作成
    class JudgeGE:
        subtotal_common = 0 # 全学共通科目(選択必修)～学部基礎(情報)30～34単位判定用のクラス変数
        subtotal_required = 0 # 全学共通科目(選択必修)～学部基礎(情報)30～34単位判定用のクラス変数
        excess_ge = 0 # 教養＋4単位判定用のクラス変数
               
        def __init__(self):
            pass
            
        # 区分2＝全学共通科目(外国語)の判定
        def judge_cat2(self):
        
            acquired_subjects_of_cat2 = AcquiredCredits.objects.filter(subject__category1=2)
            acquired_credits_cat2 = sum(acq.subject.credits for acq in acquired_subjects_of_cat2)
            self.subtotal_common += acquired_credits_cat2
            
            required_cat2 = 0
            
            if acquired_credits_cat2 >= 4:
                judge_flag2 = True
            else:
                judge_flag2 = False
                required_cat2 = 4 - acquired_credits_cat2
            self.subtotal_required += required_cat2 
            
            return acquired_credits_cat2, required_cat2, judge_flag2
            
         # 区分3＝全学共通科目(体育)の判定
        def judge_cat3(self):
                                           
            acquired_subjects_of_cat3 = AcquiredCredits.objects.filter(subject__category1=3)
            # 体育フラグ1～3の有無をチェック、変数に代入
            pe_flag_1 = acquired_subjects_of_cat3.filter(pe_flag=1).exists()
            pe_flag_2 = acquired_subjects_of_cat3.filter(pe_flag=2).exists()
            pe_flag_3 = acquired_subjects_of_cat3.filter(pe_flag=3).exists()
            acquired_credits_cat3 = sum(acq.subject.credits for acq in acquired_subjects_of_cat3)
            self.subtotal_common += acquired_credits_cat3
        
            # 初期値として未取得科目のリストを空にする
            not_acquired_subjects_cat3 = []
            required_cat3 = 0
            
            # 体育フラグの状態で判定
            if pe_flag_3 or (pe_flag_1 and pe_flag_2):
                judge_flag3 = True
            else:
                judge_flag3 = False
                # 体育フラグの状態で取得すべき科目を決定
                if pe_flag_1:
                    not_acquired_subjects_cat3.append('生涯スポーツ(種目自由:1単位)あるいは健康生涯スポーツ(2単位)')
                    required_cat3 = 1
                elif pe_flag_2:
                    not_acquired_subjects_cat3.append('健康体力づくり(1単位)あるいは健康生涯スポーツ(2単位)')
                    required_cat3 = 1
                else:
                    not_acquired_subjects_cat3.append('健康生涯スポーツ(2単位)あるいは[健康体力づくり+生涯スポーツ(種目自由)(計2単位)]')
                    required_cat3 = 2
                    
            self.subtotal_required += required_cat3
                    
            return not_acquired_subjects_cat3, acquired_credits_cat3, required_cat3, judge_flag3   
        
        # 区分4, 5＝総合科目、留学生科目の判定
        def judge_cat4_and_cat5(self):
            
            # いずれも取得単位数が全学共通科目(選択)～学部基礎の合計に算入されるのみ、要件判定はなし
            acquired_subjects_of_cat4 = AcquiredCredits.objects.filter(subject__category1=4)
            acquired_credits_cat4 = sum(acq.subject.credits for acq in acquired_subjects_of_cat4)
            acquired_subjects_of_cat5 = AcquiredCredits.objects.filter(subject__category1=5)
            acquired_credits_cat5 = sum(acq.subject.credits for acq in acquired_subjects_of_cat5)
            self.subtotal_common += (acquired_credits_cat4 + acquired_credits_cat5)
            
            return acquired_credits_cat4, acquired_credits_cat5
        
        # 区分7～9＝学部基礎(教養3分野)の判定
        def judge_cat6(self):
            acquired_subjects_of_cat6 = AcquiredCredits.objects.filter(subject__category1=6)
            acquired_credits_cat6 = sum(acq.subject.credits for acq in acquired_subjects_of_cat6)
            self.subtotal_common += acquired_credits_cat6
            
            required_cat6 = 0
            
            if acquired_credits_cat6 >= 4:
                judge_flag4 = True
                self.excess_ge += acquired_credits_cat6 - 4 # 教養＋4単位判定のために超過分を算出、クラス変数に加算
            else:
                judge_flag4 = False
                required_cat6 = 4 - acquired_credits_cat6
            self.subtotal_required += required_cat6                 
            
            return acquired_credits_cat6, required_cat6, judge_flag4
        
        def judge_cat7(self):
            acquired_subjects_of_cat7 = AcquiredCredits.objects.filter(subject__category1=7)
            acquired_credits_cat7 = sum(acq.subject.credits for acq in acquired_subjects_of_cat7)
            self.subtotal_common += acquired_credits_cat7
            
            required_cat7 = 0
                        
            if acquired_credits_cat7 >= 4:
                judge_flag5 = True
                self.excess_ge += acquired_credits_cat7 - 4
            else:
                judge_flag5 = False
                required_cat7 = 4 - acquired_credits_cat7
            self.subtotal_required += required_cat7
            
            return acquired_credits_cat7, required_cat7, judge_flag5
        
        def judge_cat8(self):
            acquired_subjects_of_cat8 = AcquiredCredits.objects.filter(subject__category1=8)
            acquired_credits_cat8 = sum(acq.subject.credits for acq in acquired_subjects_of_cat8)
            self.subtotal_common += acquired_credits_cat8
            
            required_cat8 = 0
            self.excess_ge_required = 0
            
            if acquired_credits_cat8 >= 4:
                judge_flag6 = True
                self.excess_ge += acquired_credits_cat8 - 4
            else:
                judge_flag6 = False
                required_cat8 = 4 - acquired_credits_cat8
                        
            # 学部基礎(教養）16単位の判定
            if self.excess_ge >= 4:
                judge_flag7 = True
            else:
                judge_flag7 = False
                self.excess_ge_required = 4 - self.excess_ge
            self.subtotal_required += required_cat8 + self.excess_ge_required
            
            return acquired_credits_cat8, required_cat8, judge_flag6, self.excess_ge, self.excess_ge_required, judge_flag7
        
        # 区分9＝学部基礎(情報)の判定
        def judge_cat9(self):
            acquired_subjects_of_cat9 = AcquiredCredits.objects.filter(subject__category1=9)
            acquired_credits_cat9 = sum(acq.subject.credits for acq in acquired_subjects_of_cat9)
            self.subtotal_common += acquired_credits_cat9
            
            required_cat9 = 0
            
            if acquired_credits_cat9 >= 8:
                judge_flag8 = True
            else:
                judge_flag8 = False
                required_cat9 = 8 - acquired_credits_cat9
            self.subtotal_required += required_cat9
                
            return acquired_credits_cat9, required_cat9, judge_flag8
        
        # 全学共通科目(選択必修)～学部基礎(情報)合計30～34単位の判定
        def judge_subtotal_common(self):
            if (30 <= self.subtotal_common <= 34) and (self.subtotal_required == 0):
                judge_flag9 = True
                acquired_credits_common = self.subtotal_common
            elif self.subtotal_common > 34 and self.subtotal_required == 0:
                judge_flag9 = True
                acquired_credits_common = 34
            elif self.subtotal_common + self.subtotal_required <= 34:
                judge_flag9 = False
                acquired_credits_common = self.subtotal_common
            else:
                judge_flag9 = False
                acquired_credits_common = 34 - self.subtotal_required
                
            return acquired_credits_common, self.subtotal_required, judge_flag9


# 確認画面で確定ボタン押下時にクラスで定義された判定処理～判定結果をhtmlに引き渡し、画面生成を行う処理を定義
def judgement(request):
    
    # インスタンスの作成
    judge_common = JudgeCommon()
    judge_ge = JudgeCommon.JudgeGE()
    
    # 全学共通科目の判定処理
    not_acquired_subjects_cat1, acquired_credits_cat1, required_cat1, judge_flag1 = judge_common.judge_cat1()
     
    # 全学共通科目(選択必修)～学部基礎(情報)の判定処理
    acquired_credits_cat2, required_cat2, judge_flag2 = judge_ge.judge_cat2()
    not_acquired_subjects_cat3, acquired_credits_cat3, required_cat3, judge_flag3 = judge_ge.judge_cat3()
    acquired_credits_cat4, acquired_credits_cat5 = judge_ge.judge_cat4_and_cat5()
    acquired_credits_cat6, required_cat6, judge_flag4 = judge_ge.judge_cat6()
    acquired_credits_cat7, required_cat7, judge_flag5 = judge_ge.judge_cat7()
    acquired_credits_cat8, required_cat8, judge_flag6, excess_ge, excess_ge_required, judge_flag7 = judge_ge.judge_cat8()
    acquired_credits_cat9, required_cat9, judge_flag8 = judge_ge.judge_cat9()
    acquired_credits_common, subtotal_required, judge_flag9 = judge_ge.judge_subtotal_common()
    
    
    # 'judgement.html'に引き渡すために名前を付ける
    context = {
        'not_acquired_subjects_cat1': not_acquired_subjects_cat1,
        'acquired_credits_cat1': acquired_credits_cat1,
        'required_cat1': required_cat1,
        'judge_flag1': judge_flag1,
        'acquired_credits_cat2': acquired_credits_cat2,
        'required_cat2': required_cat2,
        'judge_flag2': judge_flag2,
        'not_acquired_subjects_cat3': not_acquired_subjects_cat3,
        'acquired_credits_cat3': acquired_credits_cat3,
        'required_cat3': required_cat3,
        'judge_flag3': judge_flag3,
        'acquired_credits_cat4': acquired_credits_cat4,
        'acquired_credits_cat5': acquired_credits_cat5,
        'acquired_credits_cat6': acquired_credits_cat6,
        'required_cat6': required_cat6,
        'judge_flag4': judge_flag4,
        'acquired_credits_cat7': acquired_credits_cat7,
        'required_cat7': required_cat7,
        'judge_flag5': judge_flag5,
        'acquired_credits_cat8': acquired_credits_cat8,
        'required_cat8': required_cat8,
        'judge_flag6': judge_flag6,
        'excess_ge': excess_ge, 
        'excess_ge_required': excess_ge_required,
        'judge_flag7': judge_flag7,
        'acquired_credits_cat9': acquired_credits_cat9,
        'required_cat9': required_cat9,
        'judge_flag8': judge_flag8,
        'acquired_credits_common': acquired_credits_common,
        'subtotal_required': subtotal_required,
        'judge_flag9': judge_flag9
    }
    
    # 結果に応じた表示を返して画面生成し、HTMLレスポンスを生成
    return render(request, 'judgement.html', context)

