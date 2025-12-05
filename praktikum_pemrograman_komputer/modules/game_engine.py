from modules.data_manager import load_data_csv
import random
import time

class GameEngine:
    def __init__(self, filepath=None):
        self.question_list = load_data_csv(filepath)
        if self.question_list:
            random.shuffle(self.question_list)
        
        self.score = 0
        self.current_index = 0
        self.total_questions = len(self.question_list)
        self.lives = 3 
        
        # Mulai pencatat waktu
        self.start_time = time.time()

    def get_duration(self):
        """Mengembalikan durasi pengerjaan dalam detik"""
        return time.time() - self.start_time

    def get_current_question(self):
        if self.current_index < self.total_questions:
            return self.question_list[self.current_index]
        return None

    def check_answer(self, user_ans):
        curr = self.get_current_question()
        if not curr: return False
        
        correct = False
        kunci = curr['answer']
        tipe = curr['type']

        try:
            if tipe == "MC":
                correct = (str(user_ans) == str(kunci))
            elif tipe == "MS":
                correct = (set(user_ans) == set(kunci))
            elif tipe == "ESSAY":
                user_text = str(user_ans).lower().strip()
                kunci_text = str(kunci).lower().strip()
                correct = (user_text == kunci_text)
        except:
            correct = False

        if correct: 
            self.score += 10
        else: 
            self.lives -= 1
            
        return correct

    def next_question(self):
        self.current_index += 1
        return (self.current_index < self.total_questions and self.lives > 0)