import { useState, useEffect } from "react";
import {
  Music,
  Sparkles,
  Home,
  FileText,
  Upload,
} from "lucide-react";


export default function Web() {
  const [started, setStarted] = useState(false);

  const [tab, setTab] = useState<"home" | "my">("home");

  const [selectedFile, setSelectedFile] =
    useState<File | null>(null);

  const [feedback, setFeedback] = useState(
    "분석 버튼을 눌러 피드백을 확인하세요."
  );

  const [loading, setLoading] = useState(false);

  const [userId, setUserId] =
    useState<string>("비회원");

  const [recommendedArtists] = useState([
    {
      name: "아이유(IU)",
      genre: "Ballad",
      match: 95,
    },
    {
      name: "백예린",
      genre: "R&B",
      match: 92,
    },
    {
      name: "태연",
      genre: "Pop",
      match: 88,
    },
  ]);

  const [recommendedSongs, setRecommendedSongs] =
    useState([
      {
        title: "분석 전",
        artist: "-",
        match: 0,
      },
    ]);

  const [voiceStats, setVoiceStats] = useState([
    {
      label: "음정",
      value: 0,
      color: "#66BB6A",
    },
    {
      label: "박자",
      value: 0,
      color: "#4CAF50",
    },
    {
      label: "성량",
      value: 0,
      color: "#2F7C31",
    },
  ]);

  useEffect(() => {
    let isMounted = true;

    async function loadMobileUserInfo() {
      try {
        const res = await fetch(
          "/kiosk/current_user",
          {
            cache: "no-store",
          }
        );

        const data = await res.json();

        if (!isMounted) return;

        if (data.status === "member") {
          setUserId(data.user_id ?? "회원");
        } else if (data.status === "guest") {
          setUserId("비회원");
        }
      } catch (error) {
        console.error(
          "유저 정보 연동 실패:",
          error
        );
      }
    }

    const interval = setInterval(
      loadMobileUserInfo,
      500
    );

    loadMobileUserInfo();

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleFileChange = (
    e: React.ChangeEvent<HTMLInputElement>
  ) => {
    const file = e.target.files?.[0];

    if (file) {
      setSelectedFile(file);
    }
  };

  const uploadAndAnalyze = async () => {
    if (!selectedFile) {
      alert("파일을 선택해주세요!");
      return;
    }

    setLoading(true);

    const formData = new FormData();

    formData.append("file", selectedFile);
    formData.append("reservation_id", "1");
    formData.append(
      "reference_song",
      "No_Doubt"
    );
    formData.append("user_bpm", "120");

    try {
      const response = await fetch(
        "/songs/upload",
        {
          method: "POST",
          body: formData,
        }
      );

      const result = await response.json();

      if (result.status === "success") {
        const data = result.data;

        setFeedback(
          data.feedback || "분석 완료"
        );

        const p = Math.round(
          (data.pitch_score || 0) *
            (data.pitch_score <= 1
              ? 100
              : 1)
        );

        const t = Math.round(
          (data.tempo_score || 0) *
            (data.tempo_score <= 1
              ? 100
              : 1)
        );

        const v = Math.round(
          (data.volume_score || 0) *
            (data.volume_score <= 1
              ? 100
              : 1)
        );

        setVoiceStats([
          {
            label: "음정",
            value: p,
            color: "#66BB6A",
          },
          {
            label: "박자",
            value: t,
            color: "#4CAF50",
          },
          {
            label: "성량",
            value: v,
            color: "#2F7C31",
          },
        ]);

        setRecommendedSongs([
          {
            title:
              data.top_song || "-",
            artist:
              data.top_singer || "-",
            match: p,
          },
        ]);
      }
    } catch (e) {
      alert("분석 실패");
    } finally {
      setLoading(false);
    }
  };

  // 시작 화면
  if (!started) {
    return (
      <div className="h-screen bg-[#FAFAFA] flex flex-col items-center px-6 py-6 overflow-hidden">
        <div className="w-full max-w-lg flex flex-1 flex-col">
          <div className="w-full flex items-center justify-between">
            <span className="text-[15px] font-extrabold text-[#111111]">
              Sing Pick
            </span>

            <span className="text-xs font-medium text-gray-500">
              👤 {userId} 님
            </span>
          </div>

          <div className="flex flex-col items-center justify-center flex-1">
            <img
              src="/dist/logo.png"
              alt="Logo"
              className="w-52 h-52 object-contain"
            />
          </div>
        </div>

        <div className="w-full max-w-lg">
          <button
            onClick={() =>
              setStarted(true)
            }
            className="w-full rounded-[24px] bg-[#2F7C31] py-4 text-white font-extrabold"
          >
            결과보기
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-[#F3F7F0] flex flex-col overflow-hidden">
      
      {/* 헤더 */}
      <header className="flex-shrink-0 bg-gradient-to-br from-[#F7FBF4]/95 via-white/95 to-[#EAF4E6]/95 px-4 pb-3 pt-4 z-10">
        <div className="mx-auto flex max-w-lg items-center justify-between rounded-2xl border border-white/80 bg-white/70 px-4 py-3 shadow-sm">
          <div className="text-[13px] font-bold text-gray-800">
            ID: {userId}
          </div>

          <h2 className="text-[17px] font-extrabold text-[#111111]">
            Sing Pick!
          </h2>

          <div className="h-9 w-9 rounded-full bg-[#2F7C31]/10" />
        </div>
      </header>

      {/* 중앙 스크롤 */}
      <main
        className="
          flex-1
          overflow-y-auto
          overflow-x-hidden
          touch-pan-y
          px-5
          pt-5
          pb-40
        "
        style={{
          WebkitOverflowScrolling:
            "touch",
        }}
      >
        <div className="mx-auto max-w-lg space-y-6">
          
          {tab === "home" ? (
            <>
              {/* 추천 가수 */}
              <section>
                <h3 className="text-[13px] font-semibold mb-3 flex items-center gap-2">
                  <Music className="w-4 h-4 text-[#2F7C31]" />
                  추천 가수
                </h3>

                {recommendedArtists.map(
                  (a, i) => (
                    <div
                      key={i}
                      className="bg-white rounded-2xl p-4 border mb-2.5 flex items-center justify-between"
                    >
                      <div>
                        <h4 className="font-semibold text-[15px]">
                          {a.name}
                        </h4>

                        <p className="text-xs text-gray-500">
                          {a.genre}
                        </p>
                      </div>

                      <span className="text-xs font-bold text-[#2F7C31] bg-green-50 px-2 py-1 rounded-full">
                        {a.match}%
                      </span>
                    </div>
                  )
                )}
              </section>

              {/* 추천 곡 */}
              <section>
                <h3 className="text-[13px] font-semibold mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#2F7C31]" />
                  추천 곡
                </h3>

                {recommendedSongs.map(
                  (s, i) => (
                    <div
                      key={i}
                      className="bg-white rounded-2xl p-4 border flex items-center justify-between"
                    >
                      <div>
                        <h4 className="font-semibold text-[15px]">
                          {s.title}
                        </h4>

                        <p className="text-xs text-gray-500">
                          {s.artist}
                        </p>
                      </div>

                      <span className="text-xs font-bold text-[#2F7C31] bg-green-50 px-2 py-1 rounded-full">
                        {s.match}%
                      </span>
                    </div>
                  )
                )}
              </section>

              {/* AI 피드백 */}
              <section className="bg-white rounded-2xl p-5 border">
                <h3 className="text-[13px] font-semibold mb-4">
                  AI 상세 피드백
                </h3>

                <p className="text-[14px] text-gray-700 whitespace-pre-wrap">
                  {loading
                    ? "분석중..."
                    : feedback}
                </p>
              </section>

              {/* 음성 그래프 */}
              <section className="bg-white rounded-2xl p-5 border">
                <h3 className="text-[13px] font-semibold mb-5">
                  내 음성 그래프
                </h3>

                {voiceStats.map((s) => (
                  <div
                    key={s.label}
                    className="mb-4"
                  >
                    <div className="flex justify-between mb-1">
                      <span className="text-[13px]">
                        {s.label}
                      </span>

                      <span
                        className="text-[13px] font-bold"
                        style={{
                          color: s.color,
                        }}
                      >
                        {s.value}%
                      </span>
                    </div>

                    <div className="w-full h-2 bg-gray-100 rounded-full">
                      <div
                        className="h-full rounded-full transition-all duration-500"
                        style={{
                          width: `${s.value}%`,
                          backgroundColor:
                            s.color,
                        }}
                      />
                    </div>
                  </div>
                ))}
              </section>

              {/* 업로드 */}
              <section className="bg-white rounded-2xl p-5 border">
                <label className="w-full border-2 border-dashed rounded-2xl p-6 flex flex-col items-center cursor-pointer mb-4">
                  <Upload className="w-8 h-8 text-[#2F7C31] mb-2" />

                  <span className="text-sm text-center break-all">
                    {selectedFile
                      ? selectedFile.name
                      : "녹음 파일 선택"}
                  </span>

                  <input
                    type="file"
                    accept="audio/*"
                    onChange={
                      handleFileChange
                    }
                    className="hidden"
                  />
                </label>

                <button
                  onClick={
                    uploadAndAnalyze
                  }
                  disabled={loading}
                  className="w-full bg-[#2F7C31] text-white py-4 rounded-2xl font-bold active:scale-[0.98] transition"
                >
                  {loading
                    ? "분석중..."
                    : "분석 시작하기"}
                </button>
              </section>
            </>
          ) : (
            <div className="bg-white rounded-2xl p-16 border flex items-center justify-center text-gray-400">
              등록예정
            </div>
          )}
        </div>
      </main>

      {/* 하단 네비게이션 */}
      <nav
        className="
          fixed
          bottom-0
          left-0
          right-0
          w-full
          border-t
          border-[#DDEAD8]
          bg-white/95
          backdrop-blur-xl
          z-[9999]
          shadow-[0_-8px_24px_rgba(0,0,0,0.08)]
          pb-[max(env(safe-area-inset-bottom),12px)]
          pt-3
        "
      >
        <div className="mx-auto flex max-w-lg items-center justify-around px-4">
          
          {/* HOME */}
          <button
            onClick={() =>
              setTab("home")
            }
            className="flex flex-col items-center justify-center gap-1 py-2"
          >
            <Home
              className={`
                h-7 w-7 transition-all duration-200
                ${
                  tab === "home"
                    ? "text-[#2F7C31]"
                    : "text-gray-400"
                }
              `}
              strokeWidth={2.3}
            />

            <span
              className={`
                text-[12px] transition-all
                ${
                  tab === "home"
                    ? "text-[#2F7C31] font-bold"
                    : "text-gray-400"
                }
              `}
            >
              Home
            </span>
          </button>

          {/* MY PAGE */}
          <button
            onClick={() =>
              setTab("my")
            }
            className="flex flex-col items-center justify-center gap-1 py-2"
          >
            <FileText
              className={`
                h-7 w-7 transition-all duration-200
                ${
                  tab === "my"
                    ? "text-[#2F7C31]"
                    : "text-gray-400"
                }
              `}
              strokeWidth={2.3}
            />

            <span
              className={`
                text-[12px] transition-all
                ${
                  tab === "my"
                    ? "text-[#2F7C31] font-bold"
                    : "text-gray-400"
                }
              `}
            >
              My Page
            </span>
          </button>
        </div>
      </nav>
    </div>
  );
}