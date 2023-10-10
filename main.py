import tkinter as tk
from tkinter import ttk
from collections import Counter
import threading
import time
import numpy as np
import random


def create_color_as_hex():
    # Create a random color for the buttons
    # TODO: Do we want to create another color spectrum?
    r = lambda: random.randint(10, 100)  # These are arbitrary values (just below 128 to make it look darker).
    return '#%02X%02X%02X' % (r(), r(), r())


class SurveyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Survey App")
        self.root.configure(bg="black", )
        self.root.wm_attributes('-fullscreen', 1)

        def unmap(event):
            if event.widget is root:
                root.deiconify()

        root.protocol('WM_DELETE_WINDOW', lambda: None)  # prevent closing
        root.bind('<Unmap>', unmap)  # redisplay window when it's minimized

        self.result_labels = []
        self.song_options = []
        self.answers = {}
        self.song_idx = 0
        ttk.Label(root, text="", padding=10, background="black").pack()
        self.currently_playing_label = ttk.Label(root, text=f"Currently playing: {self.currently_playing()}",
                                                 padding=10,  #
                                                 background="dark blue", foreground="white", font=("Arial", 20),
                                                 borderwidth=10,
                                                 relief=tk.RAISED, )
        self.currently_playing_label.pack()
        self.question_label = ttk.Label(root, text="Welcher Song als nächstes?", padding=20,
                                        background="dark blue", foreground="white", font=("Arial", 30), borderwidth=10,
                                        relief=tk.RAISED, )
        self.question_label.pack()
        ttk.Label(root, text="\n", padding=10, background="black").pack()

        self.song_options_buttons = []
        self.update_next_songs()

        for i, option in enumerate(self.song_options):
            check_button = VotingButton(root, text=option, option=option)
            check_button.pack()
            self.song_options_buttons.append((option, check_button))

        self.vote_timer = None
        self.vote_countdown = None

        self.countdown_label = ttk.Label(self.root, text=f"Voting ends in {self.vote_countdown} seconds",
                                         background="black", foreground="white", font=("Arial", 14))
        # This is the initialization of the question
        self.next_survey()

    def update_next_songs(self):
        """
        This function is called to receive the new song options from spotify
        """
        # We fetch some random new songs here (from spotify)
        lst = []
        n_songs = np.random.randint(3, 7)
        for idx in range(1, n_songs):
            letter = "abcdefghijklmnopqrstuvwxyz"[np.random.randint(26)]
            n_letters = np.random.randint(3, 50)
            lst.append(letter * n_letters)
        self.song_options = lst

    def currently_playing(self):
        return f"Song no {np.random.randint(1, 1000)}"

    def next_survey(self):
        """
        This function is called to start the next song.
        It updates the optics and starts the timers for the next song and the voting.
        """

        # Reset all buttons and labels
        for label in self.result_labels:
            label.destroy()
        self.result_labels, self.answers = [], {}

        for option, check_button in self.song_options_buttons:
            check_button.destroy()
        self.song_options_buttons = []

        # TODO: Put old Song to self.played_songs

        # TODO: Obtain new Song-Guesses here. Partially Done
        self.update_next_songs()

        # TODO: Obtain new Song and set it to self.current_song
        # TODO: Set new times from current song
        vote_time = 3
        song_time = 12
        self.song_idx += 1
        self.currently_playing_label.config(text=f"Currently playing: {self.currently_playing()}")

        # Do the timing of the next song and the voting
        song_timer = threading.Timer(song_time, self.next_survey)
        voting_timer = threading.Timer(vote_time, self.vote)
        song_timer.start()
        voting_timer.start()

        # Print new Song-Buttons
        for i, option in enumerate(self.song_options):
            check_button = VotingButton(root, text=option, option=option)
            check_button.pack()
            self.song_options_buttons.append((option, check_button))
        self.vote_timer = threading.Timer(5, self.show_results)
        # TODO: Get the new timer-time as time of the next song in the queue minus 10 seconds
        # self.vote_timer.start()

    def vote(self):
        """
        This function is called when the voting starts. It starts a timer for the voting and updates the countdown_label
        We always call it in a new thread, so that the main thread can continue with its business.
        """
        self.vote_timer = threading.Timer(5, self.show_results)
        self.vote_timer.start()
        self.vote_countdown = 5
        self.update_countdown_label()

    def update_countdown_label(self):
        """
        This function updates the countdown_label. It is called every second by the vote function.
        """
        self.countdown_label.destroy()
        if self.vote_countdown > 0:
            self.countdown_label = ttk.Label(self.root, text=f"Voting ends in {self.vote_countdown} seconds",
                                             background="black", foreground="white", font=("Arial", 14))
            self.countdown_label.pack()
            self.vote_countdown -= 1
            self.root.after(1000, self.update_countdown_label)

    def show_results(self):
        """
        This function is called when the voting ends. It shows the results of the voting.
        It is still called upon in the thread of the vote_timer, so we can't do any GUI stuff here.
        """
        # Stop the vote_timer
        if self.vote_timer is not None:
            self.vote_timer.cancel()
        buttons = [check_button for option, check_button in self.song_options_buttons]

        # Count the votes
        for button in buttons:
            self.answers[button.text] = button.count

        all_answers = list(self.answers.items())
        all_answers.sort(key=lambda x: x[1], reverse=True)

        # We keep track of the results in self.result_labels, so we can delete them later
        self.result_label = ttk.Label(self.root, text="Results:",
                                      background="black",
                                      foreground="white",
                                      font=("Arial", 16))
        self.result_labels.append(self.result_label)
        self.result_labels[-1].pack()

        # Produce the new labels for the results
        for answer, count in all_answers:
            result_text = f"{answer}: {count} votes"
            self.result_labels.append(
                ttk.Label(self.root, text=result_text, background="black", foreground="white",
                          font=("Arial", 14)))

            self.result_labels[-1].pack()


class VotingButton(tk.Button):
    """
    These are the buttons for voting. They have a different style than the Labels on Top.
    """

    def __init__(self, master, text, option):
        super().__init__(master, text=text, command=self.toggle)
        self.text = text
        self.option = option
        self.selected = False
        self.configure(relief=tk.RAISED, borderwidth=20, font=("Arial", 20), background=create_color_as_hex(),
                       foreground="white",
                       activebackground=create_color_as_hex())
        self.count = 0

    def toggle(self):
        self.selected = not self.selected
        if self.selected:
            self.configure(relief="sunken")
            self.count += 1
            self.configure(relief="raised")

    def is_selected(self):
        return self.selected

    def get_option(self):
        return self.option

    def return_count(self):
        return self.count


if __name__ == "__main__":
    root = tk.Tk()
    app = SurveyApp(root)
    root.mainloop()
