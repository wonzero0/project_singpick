// 큐알코드로 보여지는 웹사이트

import { useState } from "react";
import { Music, Mic2, Upload, Sparkles } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from "recharts";
import { motion } from "motion/react";

export default function App() {
  const [selectedFile, setSelectedFile] = useState<string | null>(null);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file.name);
    }
  };

  const recommendedArtists = [
    { name: "아이유", initial: "IU" },
    { name: "박효신", initial: "PH" },
    { name: "벤", initial: "Ben" },
    { name: "태연", initial: "TY" },
    { name: "폴킴", initial: "PK" },
  ];

  const recommendedSongs = [
    { title: "너의 의미", artist: "아이유" },
    { title: "야생화", artist: "박효신" },
    { title: "열애중", artist: "벤" },
    { title: "사계", artist: "태연" },
    { title: "모든 날, 모든 순간", artist: "폴킴" },
  ];

  const voiceAnalysis = [
    { name: "음정", value: 85, color: "#60A5FA" },
    { name: "박자", value: 78, color: "#818CF8" },
    { name: "고음", value: 72, color: "#A78BFA" },
    { name: "저음", value: 88, color: "#C084FC" },
  ];

  return (
    <div
      className="min-h-screen w-full overflow-x-hidden"
      style={{
        fontFamily: "'Montserrat', -apple-system, BlinkMacSystemFont, sans-serif",
        background: "linear-gradient(135deg, #0F172A 0%, #1E293B 50%, #334155 100%)",
      }}
    >
      {/* Decorative gradient orbs */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 right-0 w-96 h-96 bg-blue-500/20 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 left-0 w-96 h-96 bg-purple-500/20 rounded-full blur-3xl"></div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-md mx-auto pb-32">
        {/* Top Bar */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center justify-between px-5 py-6"
        >
          <span className="text-white/60 text-sm">ID: user123</span>
          <h1 className="text-2xl font-bold text-white tracking-tight">
            Sing Pick
          </h1>
          <div className="w-16"></div>
        </motion.div>

        {/* Recommended Artists Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.1 }}
          className="px-5 mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Music className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">추천 가수</h2>
          </div>
          <div className="flex gap-3 overflow-x-auto scrollbar-hide pb-2">
            {recommendedArtists.map((artist, index) => (
              <motion.div
                key={artist.name}
                initial={{ opacity: 0, scale: 0.9 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.2 + index * 0.05 }}
                className="flex-shrink-0 w-24"
                style={{
                  background: "rgba(255, 255, 255, 0.05)",
                  backdropFilter: "blur(10px)",
                  border: "1px solid rgba(255, 255, 255, 0.1)",
                  borderRadius: "20px",
                  padding: "16px",
                  boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
                }}
              >
                <div
                  className="w-12 h-12 rounded-full mx-auto mb-2 flex items-center justify-center text-white font-semibold"
                  style={{
                    background: "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)",
                  }}
                >
                  {artist.initial}
                </div>
                <p className="text-white text-xs text-center truncate">{artist.name}</p>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* Recommended Songs Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
          className="px-5 mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Sparkles className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">추천 곡</h2>
          </div>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "24px",
              padding: "20px",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
            }}
          >
            {recommendedSongs.map((song, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.4 + index * 0.05 }}
                className="flex items-center gap-3 py-3"
                style={{
                  borderBottom: index < recommendedSongs.length - 1 ? "1px solid rgba(255, 255, 255, 0.05)" : "none",
                }}
              >
                <div
                  className="w-10 h-10 rounded-full flex items-center justify-center text-white text-sm font-semibold flex-shrink-0"
                  style={{
                    background: "linear-gradient(135deg, #60A5FA 0%, #A78BFA 100%)",
                  }}
                >
                  {index + 1}
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-white font-medium text-sm truncate">{song.title}</p>
                  <p className="text-white/60 text-xs truncate">{song.artist}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>

        {/* AI Detailed Feedback Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
          className="px-5 mb-6"
        >
          <div className="flex items-center gap-2 mb-4">
            <Mic2 className="w-5 h-5 text-blue-400" />
            <h2 className="text-lg font-semibold text-white">AI 상세 피드백</h2>
          </div>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "24px",
              padding: "24px",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
            }}
          >
            <div className="space-y-4">
              <div>
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold mb-2"
                  style={{
                    background: "linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)",
                    color: "white",
                  }}
                >
                  음정
                </span>
                <p className="text-white/80 text-sm leading-relaxed">
                  전반적으로 <span className="text-blue-300 font-semibold">안정적인 음정</span>을 유지하고 있습니다.
                  고음 구간에서 약간의 떨림이 있으니 호흡 조절에 주의하세요.
                </p>
              </div>
              <div>
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold mb-2"
                  style={{
                    background: "linear-gradient(135deg, #8B5CF6 0%, #A78BFA 100%)",
                    color: "white",
                  }}
                >
                  박자
                </span>
                <p className="text-white/80 text-sm leading-relaxed">
                  빠른 템포 구간에서 <span className="text-purple-300 font-semibold">리듬감</span>이 우수합니다.
                  느린 파트에서는 좀 더 여유를 가지고 표현해보세요.
                </p>
              </div>
              <div>
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold mb-2"
                  style={{
                    background: "linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%)",
                    color: "white",
                  }}
                >
                  발성
                </span>
                <p className="text-white/80 text-sm leading-relaxed">
                  <span className="text-cyan-300 font-semibold">명료한 발음</span>과 깔끔한 발성이 돋보입니다.
                  감정 표현에 더 집중하면 완성도가 높아질 것입니다.
                </p>
              </div>
              <div>
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold mb-2"
                  style={{
                    background: "linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%)",
                    color: "white",
                  }}
                >
                  표현력
                </span>
                <p className="text-white/80 text-sm leading-relaxed">
                  곡의 감정을 잘 살리고 있습니다. <span className="text-pink-300 font-semibold">다이나믹</span>한
                  표현을 더해 청중의 마음을 사로잡아보세요.
                </p>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Voice Analysis Graph Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="px-5 mb-6"
        >
          <h2 className="text-lg font-semibold text-white mb-4">내 음성 분석 그래프</h2>
          <div
            style={{
              background: "rgba(255, 255, 255, 0.05)",
              backdropFilter: "blur(10px)",
              border: "1px solid rgba(255, 255, 255, 0.1)",
              borderRadius: "24px",
              padding: "24px",
              boxShadow: "0 8px 32px rgba(0, 0, 0, 0.1)",
            }}
          >
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={voiceAnalysis} layout="vertical">
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis
                  type="category"
                  dataKey="name"
                  width={50}
                  tick={{ fill: "rgba(255, 255, 255, 0.7)", fontSize: 13 }}
                  axisLine={false}
                  tickLine={false}
                />
                <Bar dataKey="value" radius={[0, 12, 12, 0]} barSize={28}>
                  {voiceAnalysis.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
            <div className="grid grid-cols-2 gap-3 mt-4">
              {voiceAnalysis.map((metric, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ background: metric.color }}
                  ></div>
                  <span className="text-white/80 text-xs">{metric.name}</span>
                  <span className="text-white font-semibold text-sm ml-auto">{metric.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </motion.div>
      </div>

      {/* Bottom Sticky Section */}
      <motion.div
        initial={{ opacity: 0, y: 50 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.7 }}
        className="fixed bottom-0 left-0 right-0 z-20"
        style={{
          background: "rgba(15, 23, 42, 0.95)",
          backdropFilter: "blur(20px)",
          borderTop: "1px solid rgba(255, 255, 255, 0.1)",
        }}
      >
        <div className="max-w-md mx-auto px-5 py-6 space-y-3">
          <label
            htmlFor="file-upload"
            className="flex items-center justify-center gap-3 w-full py-4 rounded-2xl cursor-pointer transition-all hover:scale-[1.02]"
            style={{
              background: "rgba(255, 255, 255, 0.08)",
              border: "1.5px dashed rgba(255, 255, 255, 0.2)",
            }}
          >
            <Upload className="w-5 h-5 text-white/70" />
            <span className="text-white/70 text-sm font-medium">
              {selectedFile || "녹음 파일 선택"}
            </span>
            <input
              id="file-upload"
              type="file"
              accept="audio/*"
              onChange={handleFileSelect}
              className="hidden"
            />
          </label>

          <button
            disabled={!selectedFile}
            className="w-full py-4 rounded-2xl font-semibold text-white transition-all hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:scale-100"
            style={{
              background: selectedFile
                ? "linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%)"
                : "rgba(255, 255, 255, 0.1)",
              boxShadow: selectedFile
                ? "0 8px 24px rgba(59, 130, 246, 0.3)"
                : "none",
            }}
          >
            분석하기
          </button>
        </div>
      </motion.div>

      <style>{`
        .scrollbar-hide::-webkit-scrollbar {
          display: none;
        }
        .scrollbar-hide {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
      `}</style>
    </div>
  );
}
