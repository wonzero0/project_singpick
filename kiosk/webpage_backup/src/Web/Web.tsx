import { useState, useEffect } from "react";
import {
  Music,
  Sparkles,
  Home,
  FileText,
  Upload,
} from "lucide-react";

// 백엔드 주소 설정
const SERVER_IP = import.meta.env.VITE_BACKEND_ORIGIN || "http://192.168.0.189:8000";

export default function Web() {
  const [started, setStarted] = useState(false);
  const [tab, setTab] = useState<"home" | "my">("home");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [feedback, setFeedback] = useState("분석 버튼을 눌러 피드백을 확인하세요.");
  const [loading, setLoading] = useState(false);
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

  useEffect(() => {
    let isMounted = true;
    async function loadMobileUserInfo() {
      try {
        const res = await fetch("/kiosk/current_user", { cache: "no-store" });
        const data = await res.json();
        if (!isMounted) return;
        if (data.status === "member") setUserId(data.user_id ?? "회원");
        else if (data.status === "guest") setUserId("비회원");
      } catch (error) {
        console.error("모바일 화면 유저 정보 연동 실패:", error);
      }
    }
    const interval = setInterval(loadMobileUserInfo, 500);
    loadMobileUserInfo();
    return () => { isMounted = false; clearInterval(interval); };
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
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
    formData.append("reference_song", "No_Doubt");
    formData.append("user_bpm", "120");

    try {
      const response = await fetch("/songs/upload", { method: "POST", body: formData });
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
        setRecommendedSongs([{ title: data.top_song || "추천 결과 없음", artist: data.top_singer || "분석 완료", match: pitch }]);
      }
    } catch (error) {
      console.error(error);
      alert("분석 실패");
    } finally {
      setLoading(false);
    }
  };

  if (!started) {
    return (
      <div className="h-screen bg-[#FAFAFA] flex flex-col items-center px-6 py-6">
        <div className="w-full max-w-lg flex flex-1 flex-col">
          <div className="w-full flex items-center justify-between">
            <span className="text-[15px] font-extrabold text-[#111111]">Sing Pick</span>
            <span className="text-xs font-medium text-gray-500">👤 {userId} 님</span>
          </div>
          <div className="flex flex-col items-center justify-center flex-1 py-8">
            <img src="/dist/logo.png" alt="Sing Pick Logo" className="w-52 h-52 object-contain animate-[float_3s_ease-in-out_infinite]" />
          </div>
        </div>
        <div className="mb-5 w-full max-w-lg">
          <button onClick={() => setStarted(true)} className="w-full rounded-[24px] bg-gradient-to-br from-[#6FB94F] to-[#245F27] px-6 py-4 text-white text-[18px] font-extrabold shadow-lg">
            결과보기
          </button>
        </div>
        <style>{`@keyframes float { 0%, 100% { transform: translateY(0px); } 50% { transform: translateY(-12px); } }`}</style>
      </div>
    );
  }

  return (
    // 전체 화면을 고정하고 내부 컨텐츠 영역만 스크롤 처리
    <div className="h-screen w-full flex flex-col bg-[#FAFAFA] overflow-hidden">
      
      {/* 고정 헤더 */}
      <header className="bg-white/90 backdrop-blur-xl border-b border-gray-100 flex-shrink-0">
        <div className="max-w-lg mx-auto px-5 py-4 flex items-center justify-between">
          <span className="text-xs font-medium text-gray-500">ID: {userId}</span>
          <h2 className="font-bold text-[15px]">Sing Pick</h2>
          <div className="w-14"></div>
        </div>
      </header>

      {/* 스크롤 가능한 콘텐츠 영역 */}
      <div className="flex-1 overflow-y-auto">
        {tab === "home" && (
          <main className="max-w-lg mx-auto px-5 py-5 space-y-5">
            <section>
              <h3 className="text-[13px] font-semibold mb-3 flex items-center gap-2"><Music className="w-4 h-4 text-[#2F7C31]" /> 추천 가수</h3>
              {recommendedArtists.map((a, i) => (
                <div key={i} className="bg-white rounded-2xl p-4 border mb-2.5 flex items-center justify-between">
                  <div><h4 className="font-semibold text-[15px]">{a.name}</h4><p className="text-xs text-gray-500">{a.genre}</p></div>
                  <span className="text-xs font-bold text-[#2F7C31] bg-green-50 px-2 py-1 rounded-full">{a.match}%</span>
                </div>
              ))}
            </section>

            <section>
              <h3 className="text-[13px] font-semibold mb-3 flex items-center gap-2"><Sparkles className="w-4 h-4 text-[#2F7C31]" /> 추천 곡</h3>
              {recommendedSongs.map((s, i) => (
                <div key={i} className="bg-white rounded-2xl p-4 border flex items-center justify-between">
                  <div><h4 className="font-semibold text-[15px]">{s.title}</h4><p className="text-xs text-gray-500">{s.artist}</p></div>
                  <span className="text-xs font-bold text-[#2F7C31] bg-green-50 px-2 py-1 rounded-full">{s.match}%</span>
                </div>
              ))}
            </section>

            <section className="bg-white rounded-2xl p-5 border">
              <h3 className="text-[13px] font-semibold mb-4">AI 상세 피드백</h3>
              <p className="text-[14px] text-gray-700 whitespace-pre-wrap">{loading ? "분석중..." : feedback}</p>
            </section>

            <section className="bg-white rounded-2xl p-5 border">
              <h3 className="text-[13px] font-semibold mb-5">내 음성 그래프</h3>
              {voiceStats.map((s) => (
                <div key={s.label} className="mb-4">
                  <div className="flex justify-between mb-1"><span className="text-[13px]">{s.label}</span><span className="text-[13px] font-bold" style={{color: s.color}}>{s.value}%</span></div>
                  <div className="w-full h-2 bg-gray-100 rounded-full"><div className="h-full rounded-full" style={{width: `${s.value}%`, backgroundColor: s.color}} /></div>
                </div>
              ))}
            </section>

            <section className="bg-white rounded-2xl p-5 border">
              <label className="w-full border-2 border-dashed rounded-2xl p-6 flex flex-col items-center cursor-pointer mb-4">
                <Upload className="w-8 h-8 text-[#2F7C31] mb-2" />
                <span className="text-sm">{selectedFile ? selectedFile.name : "녹음 파일 선택"}</span>
                <input type="file" accept="audio/*" onChange={handleFileChange} className="hidden" />
              </label>
              <button onClick={uploadAndAnalyze} disabled={loading} className="w-full bg-[#2F7C31] text-white py-4 rounded-2xl font-bold">
                {loading ? "분석중..." : "분석 시작하기"}
              </button>
            </section>
          </main>
        )}

        {tab === "my" && (
          <main className="max-w-lg mx-auto px-5 py-5">
            <h3 className="text-[13px] font-semibold mb-3">과거 기록</h3>
            <div className="bg-white rounded-2xl p-16 border flex items-center justify-center text-gray-400">등록예정</div>
          </main>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <nav className="flex-shrink-0 bg-white/90 backdrop-blur-xl border-t z-50">
        <div className="max-w-lg mx-auto px-6 py-3.5 flex justify-around">
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