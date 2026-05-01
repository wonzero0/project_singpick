import { useEffect, useMemo, useRef, useState } from "react";
import { useLocation, useNavigate } from "react-router";

interface Song {
  id: number;
  title: string;
  artist: string;
}

type Stage =
  | "loading"
  | "countdown"
  | "playing"
  | "complete"
  | "error";

interface DownloadResult {
  status: string;
  message?: string;
  audio_url?: string;
}

export function Session() {
  const navigate = useNavigate();
  const location = useLocation();

  const timeoutRef = useRef<NodeJS.Timeout | null>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);

  const reservedSongs: Song[] = location.state?.reservedSongs ?? [];

  const [stage, setStage] = useState<Stage>("loading");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [countdown, setCountdown] = useState(3);
  const [audioUrl, setAudioUrl] = useState("");
  const [errorText, setErrorText] = useState("");

  const [lyrics, setLyrics] = useState<{ time: number; text: string }[]>([]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [showNextButton, setShowNextButton] = useState(false);

  const currentSong = useMemo(
    () => reservedSongs[currentIndex],
    [reservedSongs, currentIndex]
  );

  // 🎤 가사 데이터
  const lyricsMap: Record<string, { time: number; text: string }[]> = {
    "0+0": [
      { time: 0, text: "오빤 강남스타일" },
      { time: 4, text: "강남스타일~" },
      { time: 8, text: "오오오오~" },
      { time: 12, text: "에에에에~" },
      { time: 16, text: "섹시 레이디~" },
    ],
    "한숨": [
      { time: 0, text: "🎵 노래가 시작됩니다" },
      { time: 4, text: "이제 첫 번째 가사입니다" },
      { time: 8, text: "두 번째 줄입니다" },
      { time: 12, text: "후렴입니다!" },
      { time: 16, text: "마지막 가사입니다" },
    ],
  };

  // 🎵 MR 다운로드
  useEffect(() => {
    if (!currentSong) {
      setStage("complete");
      return;
    }

    let cancelled = false;

    async function prepareSong() {
      try {
        setStage("loading");

        // 🔥 핵심: 버튼 + 타이머 초기화
        setShowNextButton(false);
        if (timeoutRef.current) {
          clearTimeout(timeoutRef.current);
          timeoutRef.current = null;
        }

        setCurrentLineIndex(0);

        const res = await fetch(
          `http://127.0.0.1:8000/library/download_mr?song_info=${encodeURIComponent(
            `${currentSong.title} | ${currentSong.artist}`
          )}`
        );

        const data: DownloadResult = await res.json();

        if (cancelled) return;

        if (data.status !== "success" || !data.audio_url) {
          throw new Error("MR 다운로드 실패");
        }

        setAudioUrl(data.audio_url);
        setCountdown(3);
        setStage("countdown");
      } catch {
        if (!cancelled) setStage("error");
      }
    }

    prepareSong();

    return () => {
      cancelled = true;
    };
  }, [currentSong]);

  // 🎤 가사 설정
  useEffect(() => {
    if (!currentSong) return;

    const matched =
      Object.keys(lyricsMap).find((key) =>
        currentSong.title.includes(key)
      ) || "";

    setLyrics(lyricsMap[matched] || []);
    setCurrentLineIndex(0);
  }, [currentSong]);

  // ⏱️ 카운트다운
  useEffect(() => {
    if (stage !== "countdown") return;

    if (countdown <= 0) {
      setStage("playing");
      return;
    }

    const timer = setTimeout(() => {
      setCountdown((prev) => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [stage, countdown]);

  // 🎵 오디오 재생
  useEffect(() => {
    if (stage !== "playing") return;
    audioRef.current?.play();
  }, [stage, audioUrl]);

  // 🎤 가사 싱크
  useEffect(() => {
    if (stage !== "playing") return;
    if (!audioRef.current) return;

    const interval = setInterval(() => {
      const currentTime = audioRef.current!.currentTime;

      for (let i = 0; i < lyrics.length; i++) {
        if (
          currentTime >= lyrics[i].time &&
          (i === lyrics.length - 1 ||
            currentTime < lyrics[i + 1].time)
        ) {
          setCurrentLineIndex(i);

          // 🔥 마지막 가사 → 타이머 관리
          if (i === lyrics.length - 1) {
            if (!timeoutRef.current) {
              timeoutRef.current = setTimeout(() => {
                setShowNextButton(true);
              }, 3000);
            }
          }

          break;
        }
      }
    }, 200);

    return () => clearInterval(interval);
  }, [stage, lyrics, showNextButton]);

  const handleNextSong = () => {
    const nextIndex = currentIndex + 1;

    if (nextIndex >= reservedSongs.length) {
      setStage("complete");
      return;
    }

    setCurrentIndex(nextIndex);
  };

  const handleGoFeedback = () => {
    navigate("/feedback");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center px-8">

      {stage === "playing" && (
        <div className="w-full max-w-4xl space-y-10 text-center">

          <div>
            <div className="text-3xl font-bold">{currentSong?.title}</div>
            <div className="text-xl text-slate-300">{currentSong?.artist}</div>
          </div>

          <audio ref={audioRef} src={audioUrl} autoPlay />

          <div className="space-y-4 mt-10">
            <div className="text-4xl font-bold text-white">
              {lyrics[currentLineIndex]?.text}
            </div>
            <div className="text-2xl text-white/40">
              {lyrics[currentLineIndex + 1]?.text}
            </div>
          </div>

          {showNextButton && (
            <div className="flex justify-center mt-10">
              <button
                onClick={handleNextSong}
                className="px-8 py-4 rounded-2xl bg-gradient-to-r from-cyan-600 to-blue-600 text-xl font-bold"
              >
                다음 곡으로 넘어가기
              </button>
            </div>
          )}
        </div>
      )}

      {stage === "countdown" && (
        <div className="text-8xl text-cyan-400">{countdown}</div>
      )}

      {stage === "complete" && (
        <button
          onClick={handleGoFeedback}
          className="px-8 py-4 bg-cyan-600 rounded-xl"
        >
          피드백 확인하기
        </button>
      )}

      {stage === "error" && <div>{errorText}</div>}
    </div>
  );
}