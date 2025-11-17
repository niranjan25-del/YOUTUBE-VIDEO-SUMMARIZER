import os
import math
import glob
import logging
from typing import Dict
from urllib.parse import urlparse, parse_qs

import yt_dlp
import moviepy.editor as mp
from pydub import AudioSegment
from pydub.silence import split_on_silence
from pydub.utils import make_chunks
import speech_recognition as sr
import torch


try:
    from summarizer import Summarizer
    summarizer_available = True
except ImportError:
    summarizer_available = False
    logging.warning("Extractive summarization (Summarizer) not available.")

logger = logging.getLogger(__name__)


class VideoProcessor:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.video_path = "./videos"
        self.audio_path = "./audios"
        self.chunks_path = "./audios/chunks"

        os.makedirs(self.video_path, exist_ok=True)
        os.makedirs(self.audio_path, exist_ok=True)
        os.makedirs(self.chunks_path, exist_ok=True)

    def clean_url(self, url: str) -> str:
        """Clean YouTube URL to avoid 400 Bad Request"""
        parsed = urlparse(url)
        if 'youtu.be' in parsed.netloc:
            return url.split('?')[0].strip()
        elif 'youtube.com' in parsed.netloc:
            query = parse_qs(parsed.query)
            video_id = query.get('v', [None])[0]
            if video_id:
                return f"https://www.youtube.com/watch?v={video_id}"
        raise Exception("Invalid YouTube URL")

    def process_video(self, url: str, method: str = 'extractive', percentage: float = 0.25) -> Dict:
        try:
            logger.info(f"Processing video with method: {method}, percentage: {percentage}")
            video_path = self.download_video(url)
            audio_path = self.convert_to_audio(video_path)
            text = self.generate_text(audio_path, method)

            if method == 'abstractive':
                summary = self.generate_summary_abstractive(text, percentage)
            elif summarizer_available:
                summary = self.generate_summary_extractive(text, percentage)
            else:
                summary = "Extractive summarization not available. Please use 'abstractive'."

            self.cleanup_files()

            return {
                'text': text,
                'summary': summary,
                'method': method,
                'percentage': percentage * 100
            }

        except Exception as e:
            logger.error(f"Error in process_video: {str(e)}")
            raise

    def download_video(self, url: str) -> str:
        """Download video using yt_dlp"""
        try:
            logger.info("Downloading video with yt_dlp...")
            cleaned_url = self.clean_url(url)
            logger.info(f"Cleaned YouTube URL: {cleaned_url}")

            output_path = os.path.join(self.video_path, "%(title)s.%(ext)s")
            ydl_opts = {
                'format': 'mp4',
                'outtmpl': output_path,
                'quiet': True,
                'noplaylist': True,
                'merge_output_format': 'mp4',
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(cleaned_url, download=True)
                filename = ydl.prepare_filename(info)

            logger.info(f"Video downloaded to: {filename}")
            return filename

        except Exception as e:
            logger.error(f"yt_dlp download error: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")

    def convert_to_audio(self, video_path: str) -> str:
        """Extract audio from video and save as WAV"""
        try:
            logger.info("Converting video to audio...")
            audio_path = os.path.join(self.audio_path, "converted_audio.wav")
            clip = mp.VideoFileClip(video_path)
            clip.audio.write_audiofile(audio_path, codec='pcm_s16le', verbose=False, logger=None)
            clip.close()
            return audio_path
        except Exception as e:
            logger.error(f"Error converting to audio: {str(e)}")
            raise

    def generate_text(self, audio_path: str, method: str) -> str:
        """Transcribe audio to text"""
        try:
            logger.info("Transcribing audio...")
            sound = AudioSegment.from_wav(audio_path)

            if method == 'abstractive':
                chunks = make_chunks(sound, 20 * 1000)
            else:
                chunks = split_on_silence(
                    sound,
                    min_silence_len=500,
                    silence_thresh=sound.dBFS - 14,
                    keep_silence=2000
                )

            full_text = ""
            for i, chunk in enumerate(chunks, 1):
                chunk_file = os.path.join(self.chunks_path, f"chunk{i}.wav")
                chunk.export(chunk_file, format="wav")
                with sr.AudioFile(chunk_file) as source:
                    try:
                        audio = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio)
                        full_text += f"{text.capitalize()}. "
                    except sr.UnknownValueError:
                        logger.warning(f"Unrecognized audio in chunk {i}")
                    except sr.RequestError as e:
                        logger.error(f"Speech recognition error: {e}")

            return full_text.strip()

        except Exception as e:
            logger.error(f"Error generating text: {str(e)}")
            raise

    def generate_summary_extractive(self, text: str, ratio: float = 0.25) -> str:
        """Use BERT to generate extractive summary"""
        try:
            if not text.strip():
                return "No text available for summarization."
            logger.info("Generating extractive summary...")
            model = Summarizer('distilbert-base-uncased', hidden=[-1, -2], hidden_concat=True)
            summary = model(text, ratio=ratio)
            return summary
        except Exception as e:
            logger.error(f"Error in extractive summarization: {str(e)}")
            raise

    def generate_summary_abstractive(self, text: str, ratio: float = 0.25) -> str:
        """Use Gemini to generate abstractive summary with controlled length"""
        try:
            import google.generativeai as genai
            from dotenv import load_dotenv
            load_dotenv()
        
            print("🔑 Loaded GEMINI_API_KEY:", os.getenv("GEMINI_API_KEY"))

            logger.info("Generating abstractive summary using Gemini...")

            genai.configure(
                api_key=os.getenv("GEMINI_API_KEY")
            )

            model = genai.GenerativeModel("gemini-1.5-flash-latest")

            # Calculate target length based on ratio
            original_words = len(text.split())
            target_words = int(original_words * ratio)
        
            # Create different prompts based on the summary length
            if ratio <= 0.15:  # 10-15% - Very short summary
                length_instruction = f"Create a very concise summary in approximately {target_words} words (no more than {target_words + 20} words)"
                detail_level = "Focus only on the most essential main points."
            elif ratio <= 0.25:  # 16-25% - Short summary
                length_instruction = f"Create a brief summary in approximately {target_words} words (target: {target_words-10} to {target_words+10} words)"
                detail_level = "Include the main points and key details."
            elif ratio <= 0.35:  # 26-35% - Medium summary
                length_instruction = f"Create a moderate summary in approximately {target_words} words (target: {target_words-20} to {target_words+20} words)"
                detail_level = "Include main points, key details, and important supporting information."
            else:  # 36-50% - Detailed summary
                length_instruction = f"Create a detailed summary in approximately {target_words} words (target: {target_words-30} to {target_words+30} words)"
                detail_level = "Include main points, key details, supporting information, and relevant examples."

            prompt = f"""
                You are a professional content summarizer. Please analyze the following text and create an abstractive summary.

                REQUIREMENTS:
                - {length_instruction}
                - {detail_level}
                - Write in clear, coherent paragraphs
                - Maintain the original meaning and context
                - Use your own words (abstractive, not extractive)
                - Ensure the summary flows naturally and is well-structured

                ORIGINAL TEXT:
                    {text.strip()}

                SUMMARY:"""

            response = model.generate_content(prompt)
        
            # Verify the response length and adjust if needed
            summary = response.text.strip()
            summary_words = len(summary.split())
        
            # Log the actual vs target word count
            logger.info(f"Target words: {target_words}, Actual words: {summary_words}, Ratio achieved: {summary_words/original_words:.2%}")
        
            # If the summary is significantly shorter than expected, try to regenerate
            if summary_words < target_words * 0.7:  # If less than 70% of target
                logger.info("Summary too short, regenerating with stronger emphasis...")
            
                followup_prompt = f"""
                The previous summary was too brief ({summary_words} words). Please expand it to reach closer to {target_words} words while maintaining quality.

                Previous summary: {summary}

                Please rewrite this summary to be approximately {target_words} words by adding more detail, context, and explanation while keeping it coherent and well-structured."""
                response = model.generate_content(followup_prompt)
                summary = response.text.strip()
            
            return summary

        except Exception as e:
            logger.error(f"Error in Gemini summarization: {str(e)}")
            raise


    def cleanup_files(self):
        """Remove temporary audio/video files"""
        try:
            for file in glob.glob(os.path.join(self.chunks_path, "*.wav")):
                os.remove(file)
            for file in glob.glob(os.path.join(self.video_path, "*.mp4")):
                os.remove(file)
            logger.info("Temporary files cleaned up.")
        except Exception as e:
            logger.warning(f"Cleanup error: {str(e)}")
