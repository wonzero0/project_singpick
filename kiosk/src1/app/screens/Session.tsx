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
  { time: 0, text: "..." },
  { time: 15.5, text: "검은 눈동자의 사각지대를 찾으러 가자" },
  { time: 28.5, text: "여름 코코아, 겨울 수박도" },
  { time: 35.5, text: "혼나지 않는 파라다이스" },
  { time: 44.5, text: "앞서가는 너의 머리가" },
  { time: 51.0, text: "두 볼을 간지럽힐 때" },
  { time: 54.0, text: "나의 내일이 뛰어오네" },
  { time: 58.5, text: "난 널 버리지 않아" },
  { time: 65.0, text: "너도 같은 생각이지?" },
  { time: 72.5, text: "저 너머의 우리는" },
  { time: 78.0, text: "결코 우리가 될 수 없단다" },
  { time: 87.0, text: "영생과 영면의 차이를 너는 알고 있니?" },
  { time: 99.0, text: "멍든 발목을 꺾으려 해도" },
  { time: 105.5, text: "망설임 없이 태어나는 꿈" },
  { time: 119.0, text: "난 널 버리지 않아" },
  { time: 125.0, text: "너도 같은 생각이지?" },
  { time: 132.5, text: "저 너머의 우리는" },
  { time: 138.0, text: "결코 우리가 될 수 없단다" },
  { time: 145.0, text: "아, 난 널 버리지 않아" },
  { time: 153.0, text: "너도 같은 생각이지?" },
  { time: 160.5, text: "난 우리를 영영 잃지 않아" },
  { time: 167.0, text: "너도 영영 그럴 거지?" }
    ],

    "한숨": [
  { time: 0.0, text: "..." },
  { time: 18.3, text: "숨을 크게 쉬어봐요" },
  { time: 22.0, text: "당신의 가슴 양쪽이 저리게" },
  { time: 28.0, text: "조금은 아파올 때까지" },
  { time: 34.0, text: "숨을 더 뱉어봐요" },
  { time: 37.4, text: "당신의 안에 남은 게 없다고" },
  { time: 42.5, text: "느껴질 때까지" },
  { time: 47.7, text: "숨이 벅차올라도 괜찮아요" },
  { time: 55.2, text: "아무도 그댈 탓하진 않아" },
  { time: 63.0, text: "가끔은 실수해도 돼 누구든 그랬으니까" },
  { time: 71.0, text: "괜찮다는 말 말뿐인 위로지만" },
  { time: 82.3, text: "누군가의 한숨 그 무거운 숨을" },
  { time: 89.8, text: "내가 어떻게 헤아릴 수가 있을까요" },
  { time: 98.0, text: "당신의 한숨 그 깊일 이해할 순 없겠지만" },
  { time: 105.5, text: "괜찮아요 내가 안아줄게요" },
  { time: 125.0, text: "숨이 벅차올라도 괜찮아요" },
  { time: 132.5, text: "아무도 그댈 탓하진 않아" },
  { time: 140.5, text: "가끔은 실수해도 돼 누구든 그랬으니까" },
  { time: 148.5, text: "괜찮다는 말 말뿐인 위로지만" },
  { time: 155.7, text: "누군가의 한숨 그 무거운 숨을" },
  { time: 163.7, text: "내가 어떻게 헤아릴 수가 있을까요" },
  { time: 171.5, text: "당신의 한숨 그 깊일 이해할 순 없겠지만" },
  { time: 179.0, text: "괜찮아요 내가 안아줄게요" },
  { time: 185.7, text: "남들 눈엔 힘 빠지는" },
  { time: 189.8, text: "한숨으로 보일진 몰라도 나는 알고 있죠" },
  { time: 197.3, text: "작은 한숨 내뱉기도 어려운 하루를 보냈다는 걸" },
  { time: 204.6, text: "이제 다른 생각은 마요" },
  { time: 210.4, text: "깊이 숨을 쉬어봐요" },
  { time: 214.2, text: "그대로 내뱉어요" },
  { time: 221.7, text: "누군가의 한숨 그 무거운 숨을" },
  { time: 229.9, text: "내가 어떻게 헤아릴 수가 있을까요" },
  { time: 237.3, text: "당신의 한숨 그 깊일 이해할 순 없겠지만" },
  { time: 244.9, text: "괜찮아요 내가 안아줄게요" },
  { time: 254.0, text: "정말 수고했어요" }
    ],

    "사랑의 배터리": [     
  { time: 0, text: "..." },
  { time: 17.5, text: "나를 사랑으로 채워줘요" },
  { time: 21.0, text: "사랑의 배터리가 다 됐나 봐요" },
  { time: 24.6, text: "당신 없인 못살아 정말 나는 못살아" },
  { time: 29.0, text: "당신은 나의 배터리" },
  { time: 32.6, text: "얼짱이 아니라도 좋아요" },
  { time: 36.5, text: "몸짱이 아니라도 좋아요" },
  { time: 40.0, text: "나만을 위해줄 당신이 바로 내겐 짱이랍니다" },
  { time: 47.2, text: "한번 더 나를 안아주세요" },
  { time: 51.2, text: "가슴이 터지도록 안아주세요" },
  { time: 55.6, text: "사랑의 약발이 떨어졌나봐 당신이 필요해요" },
  { time: 61.7, text: "나를 사랑으로 채워줘요" },
  { time: 65.3, text: "사랑의 배터리가 다 됐나 봐요" },
  { time: 68.8, text: "당신 없인 못살아 정말 나는 못살아" },
  { time: 73.0, text: "당신은 나의 배터리" },
  { time: 76.0, text: "내겐 당신만이 전부예요" },
  { time: 79.6, text: "당신이 너무 좋아 완전 좋아요" },
  { time: 84.2, text: "하나뿐인 내 사랑 둘도 없는 내 사랑" },

  { time: 87.8, text: "당신이 짱이랍니다" },

  { time: 89.2, text: "사랑을 가득 넣어 주세요" },
  { time: 93.3, text: "가슴에 넘치도록 넣어주세요" },
  { time: 96.0, text: "사랑의 약발이 떨어졌나봐 나 지금 외로워요" },

  { time: 99.7, text: "나를 사랑으로 채워줘요" },
  { time: 103.3, text: "사랑의 배터리가 다 됐나 봐요" },
  { time: 106.1, text: "당신 없인 못살아 정말 나는 못살아" },
  { time: 109.9, text: "당신은 나의 배터리" },

  { time: 112.1, text: "내겐 당신만이 전부예요" },
  { time: 115.9, text: "당신이 너무 좋아 완전 좋아요" },
  { time: 118.6, text: "하나뿐인 내 사랑 둘도 없는 내 사랑" },
  { time: 120.8, text: "당신이 짱이랍니다" },

  { time: 123.1, text: "아무리 힘든 날에도 당신만 있다면" },
  { time: 126.0, text: "힘들지 않아 나는 슬프지 않아 당신 곁이라면" },

  { time: 130.2, text: "내겐 당신만이 전부예요" },
  { time: 132.9, text: "당신이 너무 좋아 완전 좋아요" },
  { time: 136.4, text: "하나뿐인 내 사랑 둘도 없는 내 사랑" },
  { time: 139.8, text: "당신이 짱이랍니다" },

  { time: 142.0, text: "당신이 짱이랍니다" },
  { time: 145.0, text: "당신이 짱이랍니다" }
    ]
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
          `/library/download_mr?song_info=${encodeURIComponent(
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
// 🎉 LED 제어
// =========================
useEffect(() => {

  // 🎵 MR 로딩 완료 → 미러볼 시작
  if (stage === "countdown") {

    fetch("/led/play", {
      method: "POST",
    });
  }

  // ⏹ 종료 → 흰 LED 복귀
  if (
    stage === "complete" ||
    stage === "error"
  ) {

    fetch("/led/stop", {
      method: "POST",
    });
  }

}, [stage]);

// =========================
// 🎵 오디오 재생
// =========================
useEffect(() => {
  if (stage !== "playing" || !audioRef.current || !audioUrl) return;

  const audioElement = audioRef.current;

  const handleAudioEnd = async () => {
    console.log(`🎵 곡 종료 - currentIndex: ${currentIndex}, 전체: ${reservedSongs.length}`);
    
    try {
      await fetch("/led/stop", {
        method: "POST",
      });
    } catch (error) {
      console.error("LED stop request failed", error);
    }

    // 현재 곡이 마지막인지 확인
    if (currentIndex >= reservedSongs.length - 1) {
      console.log("✅ 마지막 곡 완료 → Feedback 페이지로 이동");
      setTimeout(() => {
        navigate("/feedback");
      }, 500);
    } else {
      console.log("➡️ 다음 곡 대기");
      setShowNextButton(true);
    }
  };

  // 이전 리스너 제거 후 새로 등록
  audioElement.removeEventListener("ended", handleAudioEnd);
  audioElement.addEventListener("ended", handleAudioEnd, { once: true });
  
  audioElement.play().catch((error) => {
    console.error("Audio play failed", error);
  });

  return () => {
    audioElement.removeEventListener("ended", handleAudioEnd);
  };
}, [stage, currentIndex, reservedSongs.length, audioUrl, navigate]);

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
            MR 불러오는 중…
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