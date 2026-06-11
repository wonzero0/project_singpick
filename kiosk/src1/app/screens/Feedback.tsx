import { useNavigate } from "react-router-dom";
import { Star, QrCode } from "lucide-react";
import { motion } from "motion/react";
import { useEffect, useState } from "react";

export function Feedback() {
  const navigate = useNavigate();
  const [userId, setUserId] = useState("-");
  const [showExitModal, setShowExitModal] = useState(false);
  const [feedbackData, setFeedbackData] = useState<any>(null);

  // 서버 환경 설정
  const currentUrl = new URL(window.location.href);
  const configuredOrigin = import.meta.env.VITE_PUBLIC_ORIGIN;
  const configuredServerIp = import.meta.env.VITE_SERVER_IP;
  const isLocalHost =
    currentUrl.hostname === "localhost" ||
    currentUrl.hostname === "127.0.0.1" ||
    currentUrl.hostname === "192.168.0.236";

  const mobileOrigin =
    configuredOrigin ||
    (isLocalHost && configuredServerIp
      ? `${currentUrl.protocol}//${configuredServerIp}:${currentUrl.port}`
      : window.location.origin);
  
  const feedbackUrl = new URL("/web", mobileOrigin).toString();
  const qrCodeUrl = `https://api.qrserver.com/v1/create-qr-code/?size=180x180&data=${encodeURIComponent(feedbackUrl)}`;

  // 사용자 정보 로드
  useEffect(() => {
    let isMounted = true;
    async function loadUserInfo() {
      try {
        const res = await fetch("/kiosk/current_user", { cache: "no-store" });
        const data = await res.json();
        if (!isMounted) return;
        if (data.status === "member") setUserId(data.user_id ?? "-");
        else if (data.status === "guest") setUserId("비회원");
        else setUserId("-");
      } catch (error) { console.error("사용자 정보 불러오기 실패:", error); }
    }
    const interval = setInterval(loadUserInfo, 500);
    loadUserInfo();
    return () => { isMounted = false; clearInterval(interval); };
  }, []);

  // 피드백 데이터 로드 (서버 연동)
  useEffect(() => {
    const fetchFeedback = async () => {
      try {
        const res = await fetch("/session/final_result");
        const data = await res.json();
        if (data) {
          setFeedbackData(data);
        }
      } catch (err) {
        console.error("피드백 데이터를 불러올 수 없습니다:", err);
      }
    };
    fetchFeedback();
    const interval = setInterval(fetchFeedback, 1000);
    return () => clearInterval(interval);
  }, []);

  const handleGoHome = async () => {
    try {
      await fetch("/led/stop", { method: "POST" });
      const response = await fetch("/kiosk/reset", { method: "POST" });
      if (response.ok) navigate("/");
    } catch (error) {
      console.error("시스템 리셋 중 오류 발생:", error);
      navigate("/");
    }
  };

  const handleExitClick = () => { setShowExitModal(true); };

  return (
    <div className="min-h-screen w-screen overflow-y-auto overflow-x-hidden bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-950 text-white">
      
      {/* Top Bar */}
      <div className="fixed top-0 left-0 right-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/10">
        <div className="px-8 py-6 flex items-center justify-between">
          <div className="text-lg font-medium text-cyan-300">ID: {userId}</div>
          <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">Sing Pick</div>
          <button onClick={handleExitClick} className="px-5 py-2 rounded-xl bg-red-500/20 border border-red-400/40 text-red-300 hover:bg-red-500/30 transition-all font-medium">
            이용 종료
          </button>
        </div>
      </div>

      {/* Content */}
      <div className="pt-[120px] pb-12 px-8">
        <div className="max-w-4xl mx-auto space-y-6">
          
          {/* 추천 섹션 */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center"><Star size={24} /></div>
              <h2 className="text-2xl font-bold">추천 가수 / 추천 곡</h2>
            </div>
            <div className="space-y-4">
              <div className="bg-white/5 rounded-2xl p-6">
                <div className="text-cyan-300 mb-2">사용자 음성과 가장 유사한 가수 Top 1</div>
                <div className="text-3xl font-bold">{feedbackData?.top_artist || "분석 중..."}</div>
              </div>
              <div className="bg-white/5 rounded-2xl p-6">
                <div className="text-cyan-300 mb-2">사용자 음성에 가장 잘 어울리는 곡 Top 1</div>
                <div className="text-3xl font-bold">{feedbackData?.top_song || "분석 중..."}</div>
              </div>
            </div>
          </motion.div>

          {/* 한줄평 섹션 */}
          {feedbackData && (
            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 shadow-xl">
              <div className="text-cyan-300 mb-2 font-bold">노래 스타일 한줄평</div>
              <div className="text-xl">{feedbackData.feedback}</div>
            </motion.div>
          )}

          {/* QR 섹션 */}
          <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-3xl p-8 shadow-xl">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-slate-500 to-slate-600 rounded-xl flex items-center justify-center"><QrCode size={24} /></div>
              <h2 className="text-2xl font-bold">피드백 확인하기</h2>
            </div>
            <div className="bg-gradient-to-br from-slate-500/10 to-slate-600/10 border border-slate-400/30 rounded-2xl p-8 flex flex-col items-center">
              <div className="w-48 h-48 bg-white rounded-2xl flex items-center justify-center mb-4 p-4 shadow-inner">
                <img src={qrCodeUrl} alt="QR" className="w-full h-full object-contain rounded-lg" />
              </div>
              <p className="text-lg text-center text-slate-400">
                {userId !== "비회원" && userId !== "-" ? <>QR 코드를 스캔하여 <span className="text-cyan-300 font-bold"> "{userId}" </span> 님의 누적 피드백을 확인하세요.</> : <>QR 코드를 스캔하여 상세 피드백을 확인하세요.</>}
              </p>
            </div>
          </motion.div>
        </div>
      </div>

      {/* 이용 종료 모달 */}
      {showExitModal && (
        <div className="fixed inset-0 z-[100] bg-black/70 backdrop-blur-sm flex items-center justify-center px-6">
          <div className="w-full max-w-md bg-slate-900 border border-white/10 rounded-3xl p-8 shadow-2xl">
            <div className="text-2xl font-bold text-center mb-8">이용을 종료하시겠습니까?</div>
            <div className="flex gap-4">
              <button onClick={() => { setShowExitModal(false); handleGoHome(); }} className="flex-1 py-4 rounded-2xl bg-cyan-600 hover:bg-cyan-500 transition-all text-lg font-bold">예</button>
              <button onClick={() => setShowExitModal(false)} className="flex-1 py-4 rounded-2xl bg-white/10 hover:bg-white/20 transition-all text-lg font-bold">아니오</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}