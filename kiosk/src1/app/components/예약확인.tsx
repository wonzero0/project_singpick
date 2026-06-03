import { Music2, X } from "lucide-react";

interface Song {
  id: number;
  title: string;
  artist: string;
}

interface ConfirmationModalProps {
  reservedSongs: Song[];
  onConfirm: () => void;
  onCancel: () => void;
}

export function ConfirmationModal({
  reservedSongs,
  onConfirm,
  onCancel,
}: ConfirmationModalProps) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-black/80 backdrop-blur-sm"
        onClick={onCancel}
      />

      {/* Modal */}
      <div className="relative z-10 bg-gradient-to-br from-slate-900/95 to-neutral-900/95 border-2 border-cyan-400/20 rounded-3xl p-10 max-w-2xl w-full mx-8 shadow-2xl backdrop-blur-xl">
        {/* Close Button */}
        <button
          onClick={onCancel}
          className="absolute top-6 right-6 text-slate-400 hover:text-white transition-colors"
        >
          <X size={28} />
        </button>

        {/* Title */}
        <h2 className="text-3xl font-bold mb-8 text-center bg-gradient-to-r from-cyan-300 to-blue-300 bg-clip-text text-transparent">
          예약한 노래를 시작하시겠습니까?
        </h2>

        {/* Reserved Songs List */}
        <div className="space-y-3 mb-10">
          {reservedSongs.map((song, index) => (
            <div
              key={song.id}
              className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-5 flex items-center gap-4"
            >
              <div className="w-12 h-12 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center font-bold text-xl">
                {index + 1}
              </div>
              <div className="flex items-center gap-3 flex-1">
                <Music2 size={24} className="text-cyan-400" />
                <div>
                  <div className="text-lg font-medium">{song.title}</div>
                  <div className="text-sm text-slate-400">{song.artist}</div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Buttons */}
        <div className="grid grid-cols-2 gap-4">
          <button
            onClick={onCancel}
            className="py-5 rounded-2xl text-xl font-medium bg-white/5 border-2 border-white/20 hover:bg-white/10 transition-all"
          >
            취소
          </button>
          <button
            onClick={onConfirm}
            className="py-5 rounded-2xl text-xl font-bold bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 transition-all shadow-lg shadow-cyan-500/30"
          >
            확인
          </button>
        </div>
      </div>
    </div>
  );
}