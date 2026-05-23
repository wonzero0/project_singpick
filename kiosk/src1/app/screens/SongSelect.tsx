import { useState } from "react";
import { useNavigate } from "react-router-dom";

export default function SongSelect() {

  const navigate = useNavigate();

  const [count, setCount] = useState(0);

  const finish = async () => {

    if (count <= 0) {
      return;
    }

    try {

      await fetch(
        "http://127.0.0.1:8000/kiosk/entry",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            phone: localStorage.getItem("phone"),
            song_count: count,
          }),
        }
      );

      alert("곡 선택 완료");

      navigate("/reservation");

    } catch (e) {

      alert("서버 연결 실패");
    }
  };

  return (
    <div
      className="
        w-screen
        h-screen
        bg-[#DDE6ED]
        flex
        flex-col
        items-center
        justify-center
      "
    >

      {/* 전체 영역 */}
      <div
        className="
          flex
          flex-col
          items-center
          -mt-[60px]
        "
      >

        {/* 제목 */}
        <h1
          className="
            text-[58px]
            font-black
            text-black
            mb-[70px]
          "
        >
          곡 수 선택
        </h1>

        {/* 곡 수 박스 */}
        <div
          className="
            flex
            items-center
            gap-[46px]
            bg-white/40
            px-[50px]
            py-[36px]
            rounded-[36px]
            shadow-md
            mb-[60px]
          "
        >

          {/* - 버튼 */}
          <button
            onClick={() => count > 0 && setCount(count - 1)}
            className="
              w-[120px]
              h-[120px]
              rounded-full
              bg-blue-500
              text-white
              text-6xl
              font-bold
              shadow-md
              active:scale-95
              transition
            "
          >
            -
          </button>

          {/* 숫자 */}
          <div
            className="
              min-w-[180px]
              text-center
              text-[64px]
              font-black
              text-black
            "
          >
            {count}곡
          </div>

          {/* + 버튼 */}
          <button
            onClick={() => count < 3 && setCount(count + 1)}
            className="
              w-[120px]
              h-[120px]
              rounded-full
              bg-blue-500
              text-white
              text-6xl
              font-bold
              shadow-md
              active:scale-95
              transition
            "
          >
            +
          </button>

        </div>

        {/* 안내문 */}
        <div
          className="
            text-[22px]
            text-gray-700
            font-semibold
            mb-[38px]
          "
        >
          최대 3곡까지 선택 가능합니다.
        </div>

        {/* 버튼 */}
        <div className="flex gap-[28px]">

          <button
            onClick={finish}
            className="
              w-[230px]
              h-[72px]
              rounded-[22px]
              bg-[#213555]
              text-white
              text-[30px]
              font-bold
              shadow-md
              active:scale-95
              transition
            "
          >
            선택
          </button>

          <button
            onClick={() => navigate("/")}
            className="
              w-[230px]
              h-[72px]
              rounded-[22px]
              bg-[#213555]
              text-white
              text-[30px]
              font-bold
              shadow-md
              active:scale-95
              transition
            "
          >
            홈
          </button>

        </div>
      </div>
    </div>
  );
}