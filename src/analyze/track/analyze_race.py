import threading
import time

import tkinter as tk

from src.analyze.track.track_analyzer import TrackAnalyzer
from src.episode.episode import Episode
from src.graphics.track_graphics import TrackGraphics

from src.analyze.core.controls import VideoControls


class AnalyzeRace(TrackAnalyzer):

    def __init__(self, guru_parent_redraw, track_graphics :TrackGraphics, control_frame :tk.Frame):

        super().__init__(guru_parent_redraw, track_graphics, control_frame)

        self._video_controls = VideoControls(self._button_pressed, control_frame)
        self._timer = AnalyzeRace.Timer(self._draw)

        # self._race_episode = self.all_episodes[0]

    def build_control_frame(self, control_frame):
        self._video_controls.add_to_control_frame()

    def _button_pressed(self, button_type):
        if button_type == VideoControls.STOP:
            self._timer.stop()
        elif button_type == VideoControls.RESET:
            self._timer.reset()
        elif button_type == VideoControls.PLAY:
            self._timer.play()

    def redraw(self):
        self._timer.redraw()

    def _draw(self, simulation_time):
        print("Time = ", round(simulation_time, 2))
        self.track_graphics.prepare_to_remove_old_cars()
        all_done = True
        colours = ["red", "green", "blue"]
        if self.filtered_episodes:
            for i, episode in enumerate(self.filtered_episodes[0:3]):
                self._draw_episode_car(episode, simulation_time, colours[i])
                if simulation_time < episode.time_taken:
                    all_done = False
        self.track_graphics.remove_cars()
        if all_done:
            self._timer.soft_stop()

    def _draw_episode_car(self, episode: Episode, simulation_time: float, colour: str):
        event_index = episode.get_latest_event_index_on_or_before(simulation_time)
        before_event = episode.events[event_index]

        if event_index == len(episode.events) - 1:
            self.track_graphics.draw_car(before_event.x, before_event.y, colour)
        else:
            after_event = episode.events[event_index + 1]
            event_x_gap = after_event.x - before_event.x
            event_y_gap = after_event.y - before_event.y
            event_time_gap = after_event.time_elapsed - before_event.time_elapsed

            ratio = (simulation_time - before_event.time_elapsed) / event_time_gap

            x = before_event.x + ratio * event_x_gap
            y = before_event.y + ratio * event_y_gap

            self.track_graphics.draw_car(x, y, colour)

    class Timer:
        def __init__(self, redraw_callback: callable):
            self._machine_start_time = 0.0
            self._simulation_start_time = 0.0
            self._simulation_stop_time = 0.0
            self._keep_running = False
            self._is_still_running = False
            self._thread = None
            self._redraw_callback = redraw_callback

        def stop(self):
            if self._keep_running:
                self._keep_running = False
            self._thread.join(0.2)
            print(self._is_still_running)
            # stop_time = time.time()   # Sometimes gets stuck, don't know why
            # while self._is_still_running and time.time() - stop_time < 1:
            #    time.sleep(0.05)

        def soft_stop(self):
            self._keep_running = False

        def play(self):
            if not self._keep_running and not self._is_still_running:
                self._keep_running = True
                self._thread = threading.Thread(target=self._run_until_stopped)
                self._thread.daemon = True   # Set as daemon so thread is killed if main GUI is closed
                self._thread.start()

        def reset(self):
            self.stop()
            self._simulation_stop_time = 0.0
            self._simulation_start_time = 0.0
            self._redraw_callback(0.0)

        def redraw(self):
            if self._is_still_running:
                self._redraw_callback(self.get_current_simulation_time())
            else:
                self._redraw_callback(self._simulation_stop_time)

        def _run_until_stopped(self):
            self._is_still_running = True
            self._simulation_start_time = self._simulation_stop_time
            self._machine_start_time = time.time()
            while self._keep_running:
                simulation_time = self.get_current_simulation_time()
                self._redraw_callback(simulation_time)
                time.sleep(0.02)
            self._simulation_stop_time = self.get_current_simulation_time()
            self._is_still_running = False

        def get_current_simulation_time(self):
            return time.time() - self._machine_start_time + self._simulation_start_time
