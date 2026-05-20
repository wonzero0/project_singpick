import { useState, useEffect } from "react"; // 실시간 데이터 연동을 위해 useEffect 추가

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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [feedback, setFeedback] = useState("분석 버튼을 눌러 피드백을 확인하세요.");
  const [loading, setLoading] = useState(false);

  // 실시간 로그인된 사용자 ID를 관리할 State
  const [userId, setUserId] = useState<string>("비회원");

  const [recommendedArtists] = useState([
    { name: "아이유(IU)", genre: "Ballad", match: 95 },
    { name: "백예린", genre: "R&B", match: 92 },
    { name: "태연", genre: "Pop", match: 88 },
  ]);

  const [recommendedSongs, setRecommendedSongs] = useState([
    { title: "분석 전", artist: "-", match: 0 },
  ]);

  const [voiceStats, setVoiceStats] = useState([
    { label: "음정", value: 0, color: "#66BB6A" },
    { label: "박자", value: 0, color: "#4CAF50" },
    { label: "성량", value: 0, color: "#2F7C31" },
  ]);

  // 폰이 켜지자마자 키오스크 서버에서 로그인된 유저 ID를 실시간으로 훔쳐오는 로직
  useEffect(() => {
    let isMounted = true;

    async function loadMobileUserInfo() {
      try {
        // 대장님 백엔드 IP 주소와 포트를 맞춰 요청을 보냅니다.
        const res = await fetch("http://192.168.0.189:8000/kiosk/current_user", {
          cache: "no-store",
        });
        const data = await res.json();

        if (!isMounted) return;

        if (data.status === "member") {
          setUserId(data.user_id ?? "회원");
        } else if (data.status === "guest") {
          setUserId("비회원");
        }
      } catch (error) {
        console.error("모바일 화면 유저 정보 연동 실패:", error);
      }
    }

    // 0.5초마다 실시간으로 키오스크 로그인 상태를 감시합니다 (Feedback.tsx와 동일 구조)
    const interval = setInterval(loadMobileUserInfo, 500);
    loadMobileUserInfo();

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
    }
  };

  const uploadAndAnalyze = async () => {
    if (!selectedFile) {
      alert("녹음 파일을 선택해주세요!");
      return;
    }

    setLoading(true);
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("reservation_id", "1");
    // 실시간 연동된 진짜 유저 ID를 백엔드로 쏴줍니다!
    formData.append("user_id", userId); 

    try {
      const response = await fetch("http://192.168.0.189:8000/songs/upload", {
        method: "POST",
        body: formData,
      });

      const result = await response.json();

      if (result.status === "success") {
        const data = result.data;
        setFeedback(data.feedback || "AI 분석이 완료되었습니다.");

        const pitch = Math.round((data.pitch_score || 0) * (data.pitch_score <= 1 ? 100 : 1));
        const tempo = Math.round((data.tempo_score || 0) * (data.tempo_score <= 1 ? 100 : 1));
        const volume = Math.round((data.volume_score || 0) * (data.volume_score <= 1 ? 100 : 1));

        setVoiceStats([
          { label: "음정", value: pitch, color: "#66BB6A" },
          { label: "박자", value: tempo, color: "#4CAF50" },
          { label: "성량", value: volume, color: "#2F7C31" },
        ]);

        setRecommendedSongs([
          {
            title: data.top_song || "추천 결과 없음",
            artist: data.top_singer || "분석 완료",
            match: pitch,
          },
        ]);
      }
    } catch (error) {
      console.error(error);
      alert("분석 실패");
    } finally {
      setLoading(false);
    }
  };

  // 1️⃣ [시작 대기 화면]
  if (!started) {
    return (
      <div className="min-h-screen bg-[#FAFAFA] flex flex-col items-center justify-between px-8 py-12">
        <div className="flex-1 flex flex-col items-center justify-center w-full">
          {/* 상단 바 */}
          <div className="w-full flex items-center justify-between mb-16">
            <span
              className="text-[15px]"
              style={{
                fontWeight: 800,
                letterSpacing: "-0.03em",
                color: "#111111",
                fontFamily: "'Pretendard Variable', 'SUIT Variable', sans-serif",
              }}
            >
              Sing Pick
            </span>
            {/* 고정된 텍스트 대신 실제 실시간 유저 ID 상태 연동 */}
            <span className="text-xs font-medium text-gray-500">
              👤 {userId} 님
            </span>
          </div>

          {/* 로고 구역 */}
          <div className="flex flex-col items-center justify-center flex-1">
            {/* 빌드 에셋 정적 경로 보정 (/assets/logo.png) */}
            <img
              src="/dist/logo.png"
              alt="Sing Pick Logo"
              className="w-64 h-64 object-contain animate-[float_3s_ease-in-out_infinite]"
              style={{
                filter: "drop-shadow(0 25px 50px rgba(47, 124, 49, 0.25))",
              }}
            />
          </div>
        </div>

        {/* 결과보기 버튼 */}
        <div className="mb-12">
          <button
            onClick={() => setStarted(true)}
            className="w-[280px] bg-gradient-to-br from-[#A8D98B] to-[#5A8E49] text-white py-4 rounded-[20px] shadow-lg hover:shadow-xl transition-all duration-300 hover:scale-[1.02] active:scale-[0.98]"
            style={{
              fontWeight: 700,
              backgroundImage: "linear-gradient(135deg, #A8D98B 0%, #5A8E49 100%)",
              color: "#ffffff",
              border: "none",
              cursor: "pointer",
            }}
          >
            결과보기
          </button>
        </div>

        <style>{`
          @keyframes float {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-12px); }
          }
        `}</style>
      </div>
    );
  }

  // 2️⃣ [상세 분석 결과 메인 화면]
  return (
    <div className="min-h-screen bg-[#FAFAFA] pb-24">
      {/* 상단 헤더 */}
      <header className="bg-white/90 backdrop-blur-xl border-b border-gray-100 sticky top-0 z-40">
        <div className="max-w-lg mx-auto px-5 py-4 flex items-center justify-between">
          {/* 🌟 [수정 완료] 상세페이지 상단도 실시간 유저 ID 출력 */}
          <span className="text-xs font-medium text-gray-500">
            ID: {userId}
          </span>
          <h2 className="font-bold tracking-tight text-[15px]">Sing Pick</h2>
          <div className="w-14"></div>
        </div>
      </header>

      {/* HOME 탭 */}
      {tab === "home" && (
        <main className="max-w-lg mx-auto px-5 py-5 space-y-5">
          {/* 추천 가수 */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Music className="w-4 h-4 text-[#2F7C31]" />
              <h3 className="text-[13px] font-semibold text-gray-900">추천 가수</h3>
            </div>
            <div className="space-y-2.5">
              {recommendedArtists.map((artist, index) => (
                <div key={index} className="bg-white rounded-2xl p-4 border border-gray-100">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-[15px] text-gray-900 mb-0.5">{artist.name}</h4>
                      <p className="text-xs text-gray-500">{artist.genre}</p>
                    </div>
                    <div className="px-2.5 py-1 bg-gradient-to-r from-[#2F7C31]/10 to-[#66BB6A]/10 rounded-full">
                      <span className="text-xs font-bold text-[#2F7C31]">{artist.match}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* 추천 곡 */}
          <section>
            <div className="flex items-center gap-2 mb-3">
              <Sparkles className="w-4 h-4 text-[#2F7C31]" />
              <h3 className="text-[13px] font-semibold text-gray-900">추천 곡</h3>
            </div>
            <div className="space-y-2.5">
              {recommendedSongs.map((song, index) => (
                <div key={index} className="bg-white rounded-2xl p-4 border border-gray-100">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <h4 className="font-semibold text-[15px] text-gray-900 mb-0.5">{song.title}</h4>
                      <p className="text-xs text-gray-500">{song.artist}</p>
                    </div>
                    <div className="px-2.5 py-1 bg-gradient-to-r from-[#2F7C31]/10 to-[#66BB6A]/10 rounded-full">
                      <span className="text-xs font-bold text-[#2F7C31]">{song.match}%</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* AI 피드백 */}
          <section className="bg-white rounded-2xl p-5 border border-gray-100">
            <h3 className="text-[13px] font-semibold text-gray-900 mb-4">AI 상세 피드백</h3>
            <p className="text-[14px] text-gray-700 whitespace-pre-wrap leading-relaxed">
              {loading ? "AI가 목소리를 분석중입니다..." : feedback}
            </p>
          </section>

          {/* 그래프 */}
          <section className="bg-white rounded-2xl p-5 border border-gray-100">
            <h3 className="text-[13px] font-semibold text-gray-900 mb-5">내 음성 그래프</h3>
            <div className="space-y-4">
              {voiceStats.map((stat) => (
                <div key={stat.label}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-[13px] font-medium text-gray-700">{stat.label}</span>
                    <span className="text-[13px] font-bold" style={{ color: stat.color }}>{stat.value}%</span>
                  </div>
                  <div className="relative w-full h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="absolute top-0 left-0 h-full rounded-full"
                      style={{ width: `${stat.value}%`, backgroundColor: stat.color }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* 업로드 구역 */}
          <section className="bg-white rounded-2xl p-5 border border-gray-100">
            <div className="flex flex-col gap-4">
              <label className="w-full border-2 border-dashed border-gray-200 rounded-2xl p-6 flex flex-col items-center justify-center cursor-pointer hover:border-[#2F7C31] transition-all">
                <Upload className="w-8 h-8 text-[#2F7C31] mb-3" />
                <span className="text-sm text-gray-600">
                  {selectedFile ? selectedFile.name : "녹음 파일 선택"}
                </span>
                <input type="file" accept="audio/*" onChange={handleFileChange} className="hidden" />
              </label>
              <button
                onClick={uploadAndAnalyze}
                disabled={loading}
                className="w-full bg-gradient-to-br from-[#2F7C31] to-[#1B5E20] text-white py-4 rounded-2xl font-bold transition-all hover:scale-[1.01] disabled:opacity-50"
              >
                {loading ? "AI 분석중..." : "분석 시작하기"}
              </button>
            </div>
          </section>
        </main>
      )}

      {/* MY 탭 */}
      {tab === "my" && (
        <main className="max-w-lg mx-auto px-5 py-5">
          <h3 className="text-[13px] font-semibold text-gray-900 mb-3">과거 기록</h3>
          <div className="bg-white rounded-2xl p-16 border border-gray-100 flex items-center justify-center">
            <span className="text-sm text-gray-400">등록예정</span>
          </div>
        </main>
      )}

      {/* 하단 네비게이션 탭 */}
      <nav className="fixed bottom-0 left-0 right-0 bg-white/90 backdrop-blur-xl border-t border-gray-100 z-50">
        <div className="max-w-lg mx-auto px-6 py-3.5 flex justify-around items-center">
          <button onClick={() => setTab("home")} className="flex flex-col items-center gap-1.5">
            <Home className={`w-5 h-5 ${tab === "home" ? "text-[#2F7C31]" : "text-gray-400"}`} />
            <span className={`text-[11px] ${tab === "home" ? "text-[#2F7C31] font-semibold" : "text-gray-400"}`}>Home</span>
          </button>
          <button onClick={() => setTab("my")} className="flex flex-col items-center gap-1.5">
            <FileText className={`w-5 h-5 ${tab === "my" ? "text-[#2F7C31]" : "text-gray-400"}`} />
            <span className={`text-[11px] ${tab === "my" ? "text-[#2F7C31] font-semibold" : "text-gray-400"}`}>My</span>
          </button>
        </div>
      </nav>
    </div>
  );
}