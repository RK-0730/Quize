import streamlit as st
import random
import os
import csv

def load_questions(filename):
    questions = []
    
    with open(filename, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
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

def get_qa_files():
    files = [f[:-4] for f in os.listdir() if f.startswith('QA') and f.endswith('.csv')]
    return sorted(files)  # ファイル名をソート

def initialize_session_state(selected_file):
    if 'initialized' not in st.session_state or st.session_state.selected_file != selected_file:
        try:
            all_questions = load_questions(f"{selected_file}.csv")
            if not all_questions:
                st.error(f"{selected_file}.csvファイルが空です。")
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
        except FileNotFoundError:
            st.error(f"{selected_file}.csvファイルが見つかりません。")
        except Exception as e:
            st.error(f"エラーが発生しました: {str(e)}")

def reset_quiz():
    for key in list(st.session_state.keys()):
        if key != 'selected_file':
            del st.session_state[key]

def main():
    st.title("クイズアプリ")

    qa_files = get_qa_files()
    if not qa_files:
        st.error("QAファイルが見つかりません。")
        return

    selected_file = st.sidebar.selectbox("問題ファイルを選択してください", qa_files, index=0)  # index=0 を追加

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
        
        if st.button("もう一度挑戦する"):
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
        if st.button("回答する"):
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

        col1, col2 = st.columns(2)
        with col1:
            if st.button("同じ問題をやり直す"):
                st.session_state.answered = False
                st.session_state.last_answer = None
                st.session_state.last_correct = None
                _, _, st.session_state.current_options = create_quiz(st.session_state.current_question)
                st.rerun()
        
        with col2:
            if st.button("次の問題へ"):
                st.session_state.answered_questions.append(st.session_state.current_question)
                st.session_state.current_question = None
                st.session_state.current_options = None
                st.session_state.answered = False
                st.rerun()

if __name__ == "__main__":
    main()