import { useState, useEffect } from "react";
import { useNavigate } from "react-router";
import { Search, Music2, Play } from "lucide-react";
import { ConfirmationModal } from "../components/예약확인";

interface Song {
  id: number;
  title: string;
  artist: string;
  ky_number?: number;
}

export function MainReservation() {
  const navigate = useNavigate();

  const [searchQuery, setSearchQuery] = useState("");
  const [songs, setSongs] = useState<Song[]>([]);
  const [reservedSongs, setReservedSongs] = useState<Song[]>([]);
  const [showModal, setShowModal] = useState(false);
  const [userId, setUserId] = useState("-");
  const [remainingSongs, setRemainingSongs] = useState(0);
  const [lastStatus, setLastStatus] = useState("none");
  const [songsLoading, setSongsLoading] = useState(false);
  const [songsError, setSongsError] = useState("");

  useEffect(() => {
    let isMounted = true;

    async function loadUserInfo() {
      try {
        const res = await fetch("http://127.0.0.1:8000/kiosk/current_user", {
          cache: "no-store",
        });
        const data = await res.json();

        if (!isMounted) return;

        const newStatus = data.status ?? "none";

        if (newStatus === "member") {
          setUserId(data.user_id ?? "-");
          setRemainingSongs(Number(data.remaining_songs ?? 0));
        } else if (newStatus === "guest") {
          setUserId("비회원");
          setRemainingSongs(Number(data.remaining_songs ?? 0));
        } else {
          setUserId("-");
          setRemainingSongs(0);
        }

        const prevUserKey =
          lastStatus === "member"
            ? userId
            : lastStatus === "guest"
            ? "비회원"
            : "-";

        const nextUserKey =
          newStatus === "member"
            ? data.user_id ?? "-"
            : newStatus === "guest"
            ? "비회원"
            : "-";

        if (prevUserKey !== nextUserKey || newStatus === "none") {
          setReservedSongs([]);
          setShowModal(false);
        }

        setLastStatus(newStatus);
      } catch (error) {
        console.error("사용자 정보 불러오기 실패:", error);
      }
    }

    loadUserInfo();
    const interval = setInterval(loadUserInfo, 500);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [lastStatus, userId]);

  useEffect(() => {
    let cancelled = false;

    async function loadSongs() {
      try {
        setSongsLoading(true);
        setSongsError("");

        const keyword = searchQuery.trim();
        const url = keyword
          ? `http://127.0.0.1:8000/library/search?keyword=${encodeURIComponent(keyword)}`
          : "http://127.0.0.1:8000/library/search";

        const res = await fetch(url, {
          cache: "no-store",
        });

        if (!res.ok) {
          throw new Error("곡 목록 요청 실패");
        }

        const data = await res.json();

        if (cancelled) return;

        const mappedSongs: Song[] = (data.results ?? []).map((song: any) => ({
          id: song.song_id,
          title: song.title,
          artist: song.singer,
          ky_number: song.ky_number,
        }));

        setSongs(mappedSongs);
      } catch (error) {
        console.error("곡 목록 불러오기 실패:", error);
        if (!cancelled) {
          setSongs([]);
          setSongsError("곡 목록을 불러오지 못했습니다.");
        }
      } finally {
        if (!cancelled) {
          setSongsLoading(false);
        }
      }
    }

    loadSongs();

    return () => {
      cancelled = true;
    };
  }, [searchQuery]);

  const isReserved = (songId: number) => reservedSongs.some((s) => s.id === songId);

  const handleReserve = (song: Song) => {
    if (isReserved(song.id)) return;

    if (reservedSongs.length >= remainingSongs) {
      alert("예약 가능한 곡 수를 모두 사용했습니다.");
      return;
    }

    setReservedSongs((prev) => [...prev, song]);
  };

  const handleRemove = (songId: number) => {
    setReservedSongs((prev) => prev.filter((s) => s.id !== songId));
  };

  const isStartEnabled =
    remainingSongs > 0 && reservedSongs.length === remainingSongs;

  const handleStart = () => {
    if (!isStartEnabled) return;
    setShowModal(true);
  };

  const handleConfirm = () => {
    navigate("/session", {
      state: {
        reservedSongs,
        userId,
        remainingSongs,
      },
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-neutral-950 text-white flex flex-col">
      <div className="fixed top-0 left-0 right-0 z-50 bg-black/60 backdrop-blur-xl border-b border-white/10">
        <div className="px-8 py-6 flex items-center justify-between">
          <div className="text-lg font-medium text-cyan-300">
            ID: {userId}
          </div>

          <div className="text-3xl font-bold bg-gradient-to-r from-cyan-400 to-blue-400 bg-clip-text text-transparent">
            Sing Pick
          </div>

          <div className="text-lg font-medium text-cyan-300">
            {reservedSongs.length} / {remainingSongs}
          </div>
        </div>
      </div>

      <div className="fixed top-[88px] left-0 right-0 z-40 bg-gradient-to-b from-slate-950/90 to-transparent backdrop-blur-sm px-8 py-6">
        <div className="relative max-w-4xl mx-auto">
          <Search
            className="absolute left-6 top-1/2 -translate-y-1/2 text-cyan-400"
            size={24}
          />
          <input
            type="text"
            placeholder="노래 제목 또는 아티스트 검색..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-white/5 border-2 border-cyan-500/30 rounded-3xl px-16 py-5 text-xl placeholder-slate-400 focus:outline-none focus:border-cyan-400/60 transition-all"
          />
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-8 pt-[200px] pb-[120px]">
        <div className="max-w-4xl mx-auto space-y-3">
          {songsLoading && (
            <div className="text-center text-slate-300 py-10">
              곡 목록을 불러오는 중입니다...
            </div>
          )}

          {!songsLoading && songsError && (
            <div className="text-center text-red-400 py-10">
              {songsError}
            </div>
          )}

          {!songsLoading && !songsError && songs.length === 0 && (
            <div className="text-center text-slate-400 py-10">
              검색 결과가 없습니다.
            </div>
          )}

          {!songsLoading &&
            !songsError &&
            songs.map((song) => (
              <div
                key={song.id}
                className="bg-white/5 backdrop-blur-sm border border-white/10 rounded-2xl p-6 flex items-center justify-between hover:bg-white/10 transition-all group"
              >
                <div className="flex items-center gap-4 flex-1">
                  <div className="w-14 h-14 bg-gradient-to-br from-cyan-500 to-blue-600 rounded-xl flex items-center justify-center">
                    <Music2 size={28} />
                  </div>

                  <div className="flex-1">
                    <div className="text-xl font-medium mb-1">{song.title}</div>
                    <div className="text-slate-400">{song.artist}</div>
                  </div>
                </div>

                {isReserved(song.id) ? (
                  <button
                    onClick={() => handleRemove(song.id)}
                    className="px-8 py-3 bg-red-500/20 border-2 border-red-400 text-red-300 rounded-xl font-medium hover:bg-red-500/30 transition-all"
                  >
                    취소
                  </button>
                ) : (
                  <button
                    onClick={() => handleReserve(song)}
                    disabled={reservedSongs.length >= remainingSongs}
                    className={`px-8 py-3 rounded-xl font-medium transition-all ${
                      reservedSongs.length >= remainingSongs
                        ? "bg-gray-500/20 border-2 border-gray-500/30 text-gray-400 cursor-not-allowed"
                        : "bg-cyan-500/20 border-2 border-cyan-400 text-cyan-200 hover:bg-cyan-500/30"
                    }`}
                  >
                    예약
                  </button>
                )}
              </div>
            ))}
        </div>
      </div>

      <div className="fixed bottom-0 left-0 right-0 z-40 bg-gradient-to-t from-slate-950 to-transparent p-8">
        <button
          onClick={handleStart}
          disabled={!isStartEnabled}
          className={`w-full max-w-4xl mx-auto block py-7 rounded-3xl text-2xl font-bold transition-all ${
            isStartEnabled
              ? "bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 shadow-lg shadow-cyan-500/30"
              : "bg-gray-600/30 text-gray-400 cursor-not-allowed"
          }`}
        >
          <div className="flex items-center justify-center gap-3">
            <Play size={28} />
            시작하기
          </div>
        </button>
      </div>

      {showModal && (
        <ConfirmationModal
          reservedSongs={reservedSongs}
          onConfirm={handleConfirm}
          onCancel={() => setShowModal(false)}
        />
      )}
    </div>
  );
}