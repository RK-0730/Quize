import streamlit as st
import random
import csv
import requests
from io import StringIO

# GitHubのAPIエンドポイントとリポジトリ情報
GITHUB_API_URL = "https://github.com/RK-0730/Quize.git"
GITHUB_USERNAME = "RK-0730"
GITHUB_REPO = "Quize"
GITHUB_PATH = ""  # リポジトリのルートディレクトリを指定。サブディレクトリの場合は "subdirectory" のように指定
GITHUB_RAW_URL = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/{GITHUB_REPO}/main/"

def get_qa_files():
    # GitHubのリポジトリ内のCSVファイル一覧を取得する
    url = f"{GITHUB_API_URL}/{GITHUB_USERNAME}/{GITHUB_REPO}/contents/{GITHUB_PATH}"
    response = requests.get(url)
    
    if response.status_code != 200:
        st.error(f"GitHubからファイル一覧の取得に失敗しました: {response.status_code}")
        return []

    files = response.json()
    csv_files = [file['name'] for file in files if file['name'].lower().endswith('.csv')]
    
    return csv_files

def load_questions(filename):
    questions = []
    
    # GitHubからCSVファイルを読み込む
    url = GITHUB_RAW_URL + filename
    response = requests.get(url)
    if response.status_code != 200:
        st.error(f"ファイルの読み込みに失敗しました: {url}")
        return questions

    csv_file = StringIO(response.text)
    csv_reader = csv.reader(csv_file)
    next(csv_reader)  # ヘッダーをスキップ
    for row in csv_reader:
        if len(row) >= 6:  # 最低限必要な列数をチェック
            question = {
                'question': row[0],
                'answer': row[int(row[1])],  # 正解番号に対応する選択肢
                'options': row[2:],
                'answered_correctly': False
            }
            questions.append(question)
    
    return questions

def create_quiz(question_data):
    question = question_data['question']
    correct_answer = question_data['answer']
    options = question_data['options'].copy()
    
    return question, correct_answer, options

def initialize_session_state(selected_file):
    if 'initialized' not in st.session_state or st.session_state.selected_file != selected_file:
        try:
            all_questions = load_questions(selected_file)
            if not all_questions:
                st.error(f"{selected_file}ファイルが空です。")
                return
            st.session_state.questions = random.sample(all_questions, min(5, len(all_questions)))
            st.session_state.answered_questions = []
            st.session_state.wrong_answers = []
            st.session_state.current_question = None
            st.session_state.current_options = None
            st.session_state.show_result = False
            st.session_state.answered = False
            st.session_state.last_answer = None
            st.session_state.last_correct = None
            st.session_state.initialized = True
            st.session_state.selected_file = selected_file
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

def reset_quiz():
    for key in list(st.session_state.keys()):
        if key != 'selected_file':
            del st.session_state[key]

def main():
    st.set_page_config(layout="wide")
    
    st.markdown("""
    <style>
    @media (max-width: 600px) {
        .stButton>button {
            width: 100%;
        }
        .stTextField>label {
            font-size: 14px;
        }
        .stRadio>label {
            font-size: 14px;
        }
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("クイズアプリ")

    qa_files = get_qa_files()
    if not qa_files:
        st.error("CSVファイルが見つかりません。")
        return

    selected_file = st.sidebar.selectbox("問題ファイルを選択してください", qa_files)
    
    initialize_session_state(selected_file)

    if 'initialized' not in st.session_state or not st.session_state.initialized:
        return

    if not st.session_state.questions:
        st.error("問題が読み込めませんでした。")
        return

    if st.session_state.show_result:
        total_correct = sum(1 for q in st.session_state.questions if q['answered_correctly'])
        st.success(f"全ての問題に回答しました！ 正解数: {total_correct}/5")
        
        if st.session_state.wrong_answers:
            st.write("間違えた問題:")
            for wrong in st.session_state.wrong_answers:
                st.write(f"Q: {wrong['question']}")
                st.write(f"あなたの回答: {wrong['user_answer']}")
                st.write("選択肢:")
                for option in wrong['options']:
                    if option == wrong['correct_answer']:
                        st.markdown(f"- <span style='color: red;'>{option}</span>&nbsp;&nbsp;&nbsp;&nbsp;【正解】", unsafe_allow_html=True)
                    else:
                        st.write(f"- {option}")
                st.write("---")
        
        if st.button("もう一度挑戦する", key="retry"):
            reset_quiz()
            st.rerun()
        return

    if st.session_state.current_question is None:
        available_questions = [q for q in st.session_state.questions if q not in st.session_state.answered_questions]
        if not available_questions:
            st.session_state.show_result = True
            st.rerun()
        else:
            st.session_state.current_question = random.choice(available_questions)
            _, _, st.session_state.current_options = create_quiz(st.session_state.current_question)
            st.session_state.answered = False
            st.session_state.last_answer = None
            st.session_state.last_correct = None

    question, correct_answer, options = st.session_state.current_question['question'], st.session_state.current_question['answer'], st.session_state.current_options
    st.write(question)

    user_answer = st.radio("選択してください:", options, key="user_answer", index=None)

    if not st.session_state.answered:
        if st.button("回答する", key="submit"):
            st.session_state.answered = True
            st.session_state.last_answer = user_answer
            st.session_state.last_correct = correct_answer
            if user_answer == correct_answer:
                st.session_state.current_question['answered_correctly'] = True
            else:
                st.session_state.wrong_answers.append({
                    'question': question,
                    'user_answer': user_answer,
                    'correct_answer': correct_answer,
                    'options': options
                })
            st.rerun()
    else:
        if st.session_state.last_answer == st.session_state.last_correct:
            st.success("正解です！")
        else:
            st.error(f"不正解です。正解は {st.session_state.last_correct} でした。")

        if st.button("同じ問題をやり直す", key="retry_same"):
            st.session_state.answered = False
            st.session_state.last_answer = None
            st.session_state.last_correct = None
            _, _, st.session_state.current_options = create_quiz(st.session_state.current_question)
            st.rerun()
        
        if st.button("次の問題へ", key="next"):
            st.session_state.answered_questions.append(st.session_state.current_question)
            st.session_state.current_question = None
            st.session_state.current_options = None
            st.session_state.answered = False
            st.rerun()

if __name__ == "__main__":
    main()