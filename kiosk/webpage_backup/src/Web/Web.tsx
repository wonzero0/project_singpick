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
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [feedback, setFeedback] = useState("분석 버튼을 눌러 피드백을 확인하세요.");
  const [loading, setLoading] = useState(false);
  const [userId, setUserId] = useState<string>("비회원");

  // 추천 가수 상태 (데이터 연동 가능하도록 state 유지)
  const [recommendedArtists] = useState([
    { name: "비비", genre: "-", match: 82.9 },
    { name: "헤이즈", genre: "-", match: 80.9 },
    { name: "최유리", genre: "-", match: 80.6 },
  ]);

  const [recommendedSongs, setRecommendedSongs] = useState([
    { title: "일기장", artist: "비비", match: 82.9 },
    { title: "비가 오는 날엔", artist: "헤이즈", match: 80.9 },
  ]);

  const [voiceStats, setVoiceStats] = useState([
    { label: "음정", value: 85, color: "#66BB6A" },
    { label: "박자", value: 80, color: "#4CAF50" },
    { label: "성량", value: 75, color: "#2F7C31" },
  ]);

  useEffect(() => {
    let isMounted = true;
    async function loadMobileUserInfo() {
      try {
        const res = await fetch("/kiosk/current_user", { cache: "no-store" });
        const data = await res.json();
        if (!isMounted) return;
        if (data.status === "member") {
          setUserId(data.user_id ?? "회원");
        } else if (data.status === "guest") {
          setUserId("비회원");
        }
      } catch (error) {
        console.error("유저 정보 연동 실패:", error);
      }
    }
    const interval = setInterval(loadMobileUserInfo, 500);
    loadMobileUserInfo();
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  useEffect(() => {
    if (!started) return;
    async function fetchRealtimeAnalysis() {
      try {
        const targetId = userId === "비회원" ? "GUEST" : userId;
        const res = await fetch(`/result?user_id=${targetId}`);
        if (!res.ok) return;
        const data = await res.json();
        
        if (data && data.length > 0) {
          const latest = data[data.length - 1];
          if (latest.gemini_feedback) setFeedback(latest.gemini_feedback);

          const p = Math.round((latest.pitch || 0) / 4);
          const t = Math.round(latest.tempo || 0);
          const v = Math.round((latest.volume || 0) * 100);

          setVoiceStats([
            { label: "음정", value: Math.min(100, p > 0 ? p : 85), color: "#66BB6A" },
            { label: "박자", value: Math.min(100, t > 0 ? t : 80), color: "#4CAF50" },
            { label: "성량", value: Math.min(100, v > 0 ? v : 75), color: "#2F7C31" },
          ]);

          if (latest.recommendations && latest.recommendations.length > 1) {
            const restOfTop5 = latest.recommendations.slice(1, 5).map((item: any, idx: number) => ({
              title: item.title,
              artist: item.artist,
              match: 90 - (idx * 3)
            }));
            setRecommendedSongs(restOfTop5);
          }
        }
      } catch (error) {
        console.error("실시간 분석 데이터 수신 실패:", error);
      }
    }
    const interval = setInterval(fetchRealtimeAnalysis, 2000); 
    return () => clearInterval(interval);
  }, [started, userId]);

  if (!started) {
    return (
      <div className="h-screen bg-[#FAFAFA] flex flex-col items-center px-6 py-6 overflow-hidden">
        <div className="w-full max-w-lg flex flex-1 flex-col">
          <div className="w-full flex items-center justify-between">
            <span className="text-[15px] font-extrabold text-[#111111]">Sing Pick!</span>
            <span className="text-xs font-medium text-gray-500">👤 {userId} 님</span>
          </div>
          <div className="flex flex-col items-center justify-center flex-1">
            <img src="../../../public/logo.png" alt="Logo" className="w-44 h-44 object-contain" />
          </div>
        </div>
        <div className="w-full max-w-lg">
          <button onClick={() => setStarted(true)} className="w-full rounded-[24px] bg-[#2F7C31] py-5 text-white text-xl font-extrabold shadow-lg border-2 border-white" style={{ boxShadow: "0 8px 25px rgba(31, 85, 116, 0.45)" }}>
            결과보기 →
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen w-full bg-[#F3F7F0] flex flex-col overflow-hidden">
      <header className="flex-shrink-0 bg-gradient-to-br from-[#F7FBF4]/95 via-white/95 to-[#EAF4E6]/95 px-4 pb-3 pt-4 z-10">
        <div className="relative mx-auto max-w-lg rounded-3xl border border-[#DDEAD8] bg-white px-4 py-3 shadow-md">
          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-[13px] font-bold text-gray-800">ID: {userId}</div>
          <h2 className="text-center text-[26px] font-black tracking-[0.12em] text-[#2F7C31]">SINGPICK!</h2>
        </div>
      </header>

      <main className="flex-1 overflow-y-auto overflow-x-hidden touch-pan-y px-5 pt-5 pb-[220px]" style={{ WebkitOverflowScrolling: "touch" }}>
        <div className="mx-auto max-w-lg space-y-6">
          {tab === "home" ? (
            <>
              {/* 추천곡 Top 5 섹션 */}
              <section>
                <h3 className="text-[13px] font-semibold mb-3 flex items-center gap-2">
                  <Music className="w-4 h-4 text-[#2F7C31]" /> 추천곡 Top 5
                </h3>
                {recommendedSongs.map((s, i) => (
                  <div key={i} className="bg-white rounded-2xl p-4 border mb-3 flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-[15px]">{s.title}</h4>
                      <p className="text-xs text-gray-500">{s.artist}</p>
                    </div>
                    <span className="text-xs font-bold text-[#2F7C31] bg-green-50 px-2 py-1 rounded-full">{s.match}% 일치</span>
                  </div>
                ))}
              </section>

              {/* 추천가수 Top 5 섹션 */}
              <section>
                <h3 className="text-[13px] font-semibold mb-3 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-[#2F7C31]" /> 추천가수 Top 5
                </h3>
                {recommendedArtists.map((a, i) => (
                  <div key={i} className="bg-white rounded-2xl p-4 border mb-3 flex items-center justify-between">
                    <div>
                      <h4 className="font-semibold text-[15px]">{a.name}</h4>
                    </div>
                    <span className="text-xs font-bold text-[#2F7C31] bg-green-50 px-2 py-1 rounded-full">{a.match}% 추천</span>
                  </div>
                ))}
              </section>

              {/* AI 피드백 */}
              <section className="bg-white rounded-2xl p-5 border">
                <h3 className="text-[13px] font-semibold mb-4">AI 상세 피드백</h3>
                <p className="text-[14px] text-gray-700 whitespace-pre-wrap">{loading ? "분석중..." : feedback}</p>
              </section>

              {/* 음성 그래프 */}
              <section className="bg-white rounded-2xl p-5 border">
                <h3 className="text-[13px] font-semibold mb-5">내 음성 그래프</h3>
                {voiceStats.map((s) => (
                  <div key={s.label} className="mb-4">
                    <div className="flex justify-between mb-1">
                      <span className="text-[13px]">{s.label}</span>
                      <span className="text-[13px] font-bold" style={{ color: s.color }}>{s.value}%</span>
                    </div>
                    <div className="w-full h-2 bg-gray-100 rounded-full">
                      <div className="h-full rounded-full transition-all duration-500" style={{ width: `${s.value}%`, backgroundColor: s.color }} />
                    </div>
                  </div>
                ))}
              </section>
            </>
          ) : (
            <div className="bg-white rounded-2xl p-16 border flex items-center justify-center text-gray-400">등록예정</div>
          )}
        </div>
      </main>

      {/* 하단 네비게이션 */}
      <nav className="fixed bottom-0 left-0 right-0 w-full border-t border-[#DDEAD8] bg-white/95 backdrop-blur-xl z-[9999] shadow-[0_-8px_24px_rgba(0,0,0,0.08)] pb-[max(env(safe-area-inset-bottom),12px)] pt-3">
        <div className="mx-auto flex max-w-lg items-center justify-between px-12">
          <button onClick={() => setTab("home")} className="flex-1 flex flex-col items-center justify-center gap-1 py-2">
            <Home className={`h-7 w-7 transition-all duration-200 ${tab === "home" ? "text-[#2F7C31]" : "text-gray-400"}`} strokeWidth={2.3} />
            <span className={`text-[12px] transition-all ${tab === "home" ? "text-[#2F7C31] font-bold" : "text-gray-400"}`}>Home</span>
          </button>
          <button onClick={() => setTab("my")} className="flex-1 flex flex-col items-center justify-center gap-1 py-2">
            <FileText className={`h-7 w-7 transition-all duration-200 ${tab === "my" ? "text-[#2F7C31]" : "text-gray-400"}`} strokeWidth={2.3} />
            <span className={`text-[12px] transition-all ${tab === "my" ? "text-[#2F7C31] font-bold" : "text-gray-400"}`}>My Page</span>
          </button>
        </div>
      </nav>
    </div>
  );
}