import { useEffect } from "react";
import { useNavigate } from "react-router-dom";

export default function KioskHome() {

  const navigate = useNavigate();

  useEffect(() => {
    fetch("/kiosk/led", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ color: "GREEN" }),
    }).catch(() => {
      console.warn("외부 LED GREEN 명령 전송 실패");
    });
  }, []);

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

      {/* 전체 박스 */}
      <div
        className="
          flex
          flex-col
          items-center
          -mt-[80px]
        "
      >

        {/* 로고 */}
        <h1
          className="
            text-[72px]
            font-black
            tracking-tight
            text-black
            mb-[70px]
          "
        >
          SINGPICK
        </h1>

        {/* 회원가입 */}
        <button
          onClick={() => navigate("/signup")}
          className="
            w-[420px]
            h-[82px]
            rounded-[24px]
            bg-[#2F80ED]
            text-white
            text-[34px]
            font-bold
            shadow-md
            active:scale-95
            transition
            mb-[34px]
          "
        >
          회원가입
        </button>

        {/* 아래 버튼 */}
        <div className="flex gap-[28px]">

          {/* 회원 */}
          <button
            onClick={() => navigate("/login")}
            className="
              w-[195px]
              h-[78px]
              rounded-[22px]
              bg-[#0ACF4A]
              text-white
              text-[30px]
              font-bold
              shadow-md
              active:scale-95
              transition
            "
          >
            회원
          </button>

          {/* 비회원 */}
          <button
            onClick={() => {
              localStorage.removeItem("phone");
              localStorage.removeItem("user_id");

              navigate("/song");
            }}
            
            className="
              w-[195px]
              h-[78px]
              rounded-[22px]
              bg-[#74798A]
              text-white
              text-[30px]
              font-bold
              shadow-md
              active:scale-95
              transition
            "
          >
            비회원
          </button>

        </div>
      </div>
    </div>
  );
}