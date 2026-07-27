# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 언어

이 저장소에서 작업할 때는 항상 한국어로 응답할 것.

## 프로젝트 개요

KIS FICC 세일즈 담당자가 텔레그램 채널로 포맷된 메시지(텍스트, 이미지, PDF)를 발송하는 단일 파일 Streamlit 웹 앱(`contents_sender.py`). 텔레그램 Bot API를 사용하며 UI는 한국어.

## 실행 방법

```
pip install -r requirements.txt
streamlit run contents_sender.py
```

앱은 8501 포트에서 실행됨. 테스트나 린터는 설정되어 있지 않음. devcontainer(`.devcontainer/devcontainer.json`)가 attach 시 requirements 설치 후 Streamlit을 자동 실행함 (GitHub Codespaces / Streamlit Community Cloud 배포용).

## 시크릿

런타임 자격 증명은 Streamlit secrets(`st.secrets`, 로컬에서는 `.streamlit/secrets.toml`, 배포 시에는 Streamlit Cloud secrets UI — 저장소에 커밋되지 않음)에서 읽어옴:

- `APP_PASSWORD` — 앱 로그인 화면의 접근 비밀번호
- `TELEGRAM_TOKEN` — 텔레그램 봇 토큰
- `CHAT_ID` — 발송 대상 텔레그램 채팅/채널
- `FRED_API_KEY` — FRED API 키 (없으면 미국 지표 당일 발표 확인 기능만 조용히 비활성화됨)

## contents_sender.py 구조

파일은 번호가 붙은 주석 구분선(`# ── N. ...`)으로 섹션이 나뉘어 있음. 새 코드도 이 체계를 유지할 것:

1. **페이지 설정 / 세션 상태** — `st.session_state` 키: `msg_input`, `subject_input`, `authenticated`, 그리고 위젯 키 `file_up`, `use_spoiler`.
2. **비밀번호 게이트** — `check_password()`가 가장 먼저 실행되며, 인증 전에는 `st.stop()`으로 앱 전체가 차단됨.
3. **경제 이벤트 캘린더** — `FIXED_EVENTS`는 FOMC / 한국은행 금통위 일정과 국내 지표 발표일을 수동 관리하는 `date → label` 딕셔너리 (현재 2026년까지만 등록되어 있어 매년 수동으로 연장 필요). `fetch_fred_today_events()`는 FRED API를 폴링해 미국 지표의 당일 발표 여부를 확인함 (`@st.cache_data`로 1시간 캐시). `show_event_banner()`는 오늘 이벤트와 내일 예정 이벤트(D-1 예고)를 렌더링함.
4. **헬퍼 함수** — `_escape()`(텔레그램용 HTML 이스케이프), `_build_message()`(브랜드 HTML 메시지 조립: 헤더 링크, 굵은 제목, 선택적 `<tg-spoiler>` 본문), `_post()`(텔레그램 Bot API POST 래퍼).
5. **발송 로직** — `send_telegram()`이 첨부 유형에 따라 분기: 이미지는 `sendPhoto`(1장) 또는 `sendMediaGroup`(여러 장, 캡션은 첫 항목에만), 텍스트만 있으면 `sendMessage`, 이미지 외 파일은 각각 `sendDocument`로 발송. 모든 메시지는 `parse_mode: HTML` 사용.
6. **UI** — 제목/내용 입력, 스포일러 체크박스, 파일 업로더(jpg/png/pdf), `on_click`으로 `send_telegram`에 연결된 SEND 버튼.

Streamlit은 상호작용이 있을 때마다 스크립트 전체를 다시 실행함 — 최상위 코드는 매 rerun마다 실행되므로, 비용이 큰 작업은 반드시 캐시(`@st.cache_data`)하거나 세션 상태로 보호할 것.
