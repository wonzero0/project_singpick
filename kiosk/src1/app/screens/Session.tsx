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

  const audioRef = useRef<HTMLAudioElement | null>(null);

  const reservedSongs: Song[] = location.state?.reservedSongs ?? [];

  const [stage, setStage] = useState<Stage>("loading");
  const [currentIndex, setCurrentIndex] = useState(0);
  const [countdown, setCountdown] = useState(3);
  const [audioUrl, setAudioUrl] = useState("");
  const [errorText, setErrorText] = useState("");

  const [lyrics, setLyrics] = useState<
    { time: number; text: string }[]
  >([]);

  const [currentLineIndex, setCurrentLineIndex] = useState(0);

  // 🔥 핵심
  const [showNextButton, setShowNextButton] = useState(false);
  const [showFeedbackButton, setShowFeedbackButton] = useState(false);

  const currentSong = useMemo(
    () => reservedSongs[currentIndex],
    [reservedSongs, currentIndex]
  );

  // 🎤 가사 데이터
  const lyricsMap: Record<
    string,
    { time: number; text: string }[]
  > = {
    "0+0": [
      { time: 0, text: "검은 눈동자의 사각지대를 찾으러 가자" },
      { time: 5, text: "여름 코코아 겨울 수박도" },
      { time: 10, text: "혼나지 않는 파라다이스" },
    ],

    "한숨": [
      { time: 0, text: "앞서가는 너의 머리가" },
      { time: 5, text: "두 볼을 간지럽힐 때" },
      { time: 10, text: "나의 내일이 뛰어오네" },
    ],
  };

  // =========================
  // 🎵 MR 다운로드
  // =========================
  useEffect(() => {
    if (!currentSong) {
      setStage("complete");
      return;
    }

    let cancelled = false;

    async function prepareSong() {
      try {
        setStage("loading");

        setShowNextButton(false);
        setShowFeedbackButton(false);

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
        if (!cancelled) {
          setErrorText("MR 불러오기 실패");
          setStage("error");
        }
      }
    }

    prepareSong();

    return () => {
      cancelled = true;
    };
  }, [currentSong]);

  // =========================
  // 🎤 가사 설정
  // =========================
  useEffect(() => {
    if (!currentSong) return;

    const matched =
      Object.keys(lyricsMap).find((key) =>
        currentSong.title.includes(key)
      ) || "";

    setLyrics(lyricsMap[matched] || []);
    setCurrentLineIndex(0);
  }, [currentSong]);

  // =========================
  // ⏱️ 카운트다운
  // =========================
  useEffect(() => {
    if (stage !== "countdown") return;

    if (countdown <= 0) {
      setStage("playing");
      return;
    }

    const timer = setTimeout(() => {
      setCountdown((prev) => prev - 1);
    }, 800);

    return () => clearTimeout(timer);
  }, [stage, countdown]);

  // =========================
  // 🎵 오디오 재생
  // =========================
  useEffect(() => {
    if (stage !== "playing") return;

    audioRef.current?.play();

    // 🔥 핵심: MR 끝났을 때 버튼 생성
    audioRef.current!.onended = () => {
      const isLastSong =
        currentIndex === reservedSongs.length - 1;

      if (isLastSong) {
        setShowFeedbackButton(true);
      } else {
        setShowNextButton(true);
      }
    };
  }, [stage]);

  // =========================
  // 🎤 가사 싱크
  // =========================
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
          break;
        }
      }
    }, 200);

    return () => clearInterval(interval);
  }, [stage, lyrics]);

  // =========================
  // 다음 곡
  // =========================
  const handleNextSong = () => {
    setShowNextButton(false);

    const nextIndex = currentIndex + 1;

    if (nextIndex >= reservedSongs.length) {
      setStage("complete");
      return;
    }

    setCurrentIndex(nextIndex);
  };

  // =========================
  // 피드백 이동
  // =========================
  const handleGoFeedback = () => {
    navigate("/feedback");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white flex flex-col items-center justify-center px-8">

      {/* ========================= */}
      {/* 🔥 로딩 화면 */}
      {/* ========================= */}
      {stage === "loading" && (
        <div className="flex flex-col items-center gap-8">

          {/* 🔥 스피너 */}
          <div className="w-20 h-20 border-4 border-cyan-400/30 border-t-cyan-400 rounded-full animate-spin" />

          <div className="text-3xl font-bold text-cyan-300">
            엠알 불러오는 중...
          </div>

          <div className="text-xl text-slate-400">
            {currentSong?.title}
          </div>
        </div>
      )}

      {/* ========================= */}
      {/* ⏱️ 카운트다운 */}
      {/* ========================= */}
      {stage === "countdown" && (
        <div className="flex items-center justify-center">
          <div
            className="text-5xl font-bold text-cyan-300 tracking-wide"
            style={{
              animation: "flashText 0.35s infinite"
            }}
          >
            노래가 시작됩니다.
          </div>
          <style>
            {`
              @keyframes flashText {
                0% {
                  opacity: 1;
                  transform: scale(1);
                }

                50% {
                  opacity: 0.1;
                  transform: scale(1.08);
                }

                100% {
                  opacity: 1;
                  transform: scale(1);
                }
              }
            `}
    </style>

        </div>
      )}

      {/* ========================= */}
      {/* 🎵 재생 화면 */}
      {/* ========================= */}
      {stage === "playing" && (
        <div className="w-full max-w-4xl space-y-10 text-center">

          <div>
            <div className="text-3xl font-bold">
              {currentSong?.title}
            </div>

            <div className="text-xl text-slate-300">
              {currentSong?.artist}
            </div>
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

          {/* 🔥 다음곡 버튼 */}
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

          {/* 🔥 마지막 곡 */}
          {showFeedbackButton && (
            <div className="flex justify-center mt-10">
              <button
                onClick={handleGoFeedback}
                className="px-8 py-4 rounded-2xl bg-gradient-to-r from-cyan-600 to-blue-600 text-xl font-bold"
              >
                결과 확인하기
              </button>
            </div>
          )}
        </div>
      )}

      {/* ========================= */}
      {/* ❌ 에러 */}
      {/* ========================= */}
      {stage === "error" && (
        <div className="text-red-400 text-2xl">
          {errorText}
        </div>
      )}
    </div>
  );
}