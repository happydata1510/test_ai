from django.views.generic.edit import FormView
from .forms import ChatForm
from openai import OpenAI
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .models import SearchHistory
from youtube_transcript_api import YouTubeTranscriptApi


# 클라이언트 인스턴스 생성
client = OpenAI(api_key=settings.OPENAI_API_KEY)

import fitz  # PyMuPDF 라이브러리
def translate_to_korean(text, model="gpt-3.5-turbo"):
    try:
        translation_prompt = f"Translate the following text to Korean: {text}"
        translation_completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": translation_prompt}],
            max_tokens=150,
            temperature=0.5
        )
        return translation_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred during translation: {e}"

def extract_text_from_pdf(pdf_file):
    """
    PDF 파일에서 텍스트를 추출하는 함수.
    """
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

from youtube_transcript_api import YouTubeTranscriptApi

def get_completion(prompt, model="gpt-3.5-turbo"):
    try:
        chat_completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
            temperature=0.5
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {e}"

def extract_text_from_youtube(url):
    """
    YouTube URL에서 동영상의 스크립트를 추출하는 함수.
    """
    video_id = url.split('v=')[-1]  # URL에서 비디오 ID 추출
    transcript = YouTubeTranscriptApi.get_transcript(video_id)
    transcript_text = ' '.join([item['text'] for item in transcript])
    return transcript_text


# 이 부분 수정
def generate_prompt(text_input=None, file_input=None, youtube_url=None):
    if text_input:
        return f"다음 내용을 10줄 이내로 요약해줘: {text_input}"
    elif file_input:
        file_content = extract_text_from_pdf(file_input)
        return f"다음 PDF 파일 내용을 10줄 이내로 요약해줘: {file_content}"
    elif youtube_url:
        youtube_content = extract_text_from_youtube(youtube_url)
        return f"다음 YouTube 동영상 내용을 10줄 이내로 요약해줘: {youtube_content}"
    else:
        return "요약할 내용이 없습니다."
# 이 부분 수정
class ChatView(LoginRequiredMixin, FormView):
    template_name = 'chat/index.html'
    form_class = ChatForm
    success_url = '/'  # 폼 제출 후 다시 메인 페이지로 리디렉션

    def form_valid(self, form):
        text_input = form.cleaned_data.get('text_input')
        file_input = form.cleaned_data.get('file_input')
        youtube_url = form.cleaned_data.get('youtube_url')

        prompt = generate_prompt(text_input, file_input, youtube_url)
        summary_result = get_completion(prompt)

        # 영어로 출력된 요약을 한글로 번역
        translation_result = translate_to_korean(summary_result)

        # 검색 기록을 DB에 저장
        SearchHistory.objects.create(
            user=self.request.user,
            url=youtube_url,
            text_input=text_input,
            file_name=file_input.name if file_input else None,
            summary_result=summary_result,
            translation_result=translation_result,
        )

        return self.render_to_response(self.get_context_data(
            summary_result=summary_result,
            translation_result=translation_result
        ))
class HomeView(TemplateView):
    template_name = 'chat/home.html'
