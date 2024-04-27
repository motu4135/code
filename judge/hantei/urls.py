from django.urls import path
from . import views

app_name = 'hantei'

urlpatterns = [
    path('subjects/', views.subject_list, name='subject_list'),
    path('confirm_subjects/', views.confirm_subjects, name='confirm_subjects'), # 確認画面のurlを追加, URLの最後に'/'が抜けていたので追加(10/30/23)
    path('judgement/', views.judgement, name='judgement'), # 判定画面のurlを追加
]