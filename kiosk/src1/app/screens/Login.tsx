import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import NumberKeyboard from "../components/NumberKeyboard";
import { useLoginLockout } from "../hooks/useLoginLockout";

export default function Login() {

  const navigate = useNavigate();

  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const [activeInput, setActiveInput] = useState<
    "phone" | "password" | null
  >(null);

  const { isLocked, remainingSeconds, recordFailure, resetLockout } =
    useLoginLockout();

  useEffect(() => {
    fetch("/kiosk/led", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ color: "GREEN" }),
    }).catch(() => {
      console.warn("외부 LED GREEN 명령 전송 실패");
    });
  }, []);

  const login = async () => {
    if (isLocked) {
      return;
    }

    try {

      const res = await fetch(
        "/users/login",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            phone,
            password,
          }),
        }
      );

      if (res.ok) {
        const data = await res.json();

        resetLockout();

        localStorage.setItem("phone", phone);
        localStorage.setItem("user_id", data.user_id);

        navigate("/song");
      } else {
        recordFailure();
        const data = await res.json();
        setError(data.detail || "로그인 실패");
      }

    } catch {

      setError("서버 연결 실패");
    }
  };

  return (

    <div className="
      w-screen
      min-h-[100dvh]
      bg-[#DDE6ED]
      flex
      flex-col
      items-center
      justify-center
    ">

      <h1 className="text-5xl font-bold mb-8">
        회원 로그인
      </h1>

      <div className="flex flex-col gap-3">

  <div className="relative">
    <input
      type="tel"
      value={phone}
      readOnly
      placeholder="전화번호 입력"
      onClick={() => setActiveInput("phone")}
      className={`
        w-[520px]
        h-[58px]
        rounded-xl
        px-5
        text-xl
        bg-white
        border-2
        shadow-sm
        placeholder:text-gray-500
        focus:outline-none
        ${
          activeInput === "phone"
            ? "border-[#213555]"
            : "border-[#AAB7C4]"
        }
      `}
    />

    {activeInput === "phone" && (
      <span
        className="
          absolute
          top-1/2
          -translate-y-1/2
          cursor-blink
          text-xl
          font-bold
          pointer-events-none
        "
        style={{
          left: `${20 + phone.length * 12}px`,
        }}
      >
        |
      </span>
    )}
  </div>

  <div className="relative">
    <input
      type="password"
      value={password}
      readOnly
      placeholder="비밀번호 입력"
      onClick={() => setActiveInput("password")}
      className={`
        w-[520px]
        h-[58px]
        rounded-xl
        px-5
        text-xl
        bg-white
        border-2
        shadow-sm
        placeholder:text-gray-500
        focus:outline-none
        ${
          activeInput === "password"
            ? "border-[#213555]"
            : "border-[#AAB7C4]"
        }
      `}
    />

    {activeInput === "password" && (
      <span
        className="
          absolute
          top-1/2
          -translate-y-1/2
          cursor-blink
          text-xl
          font-bold
          pointer-events-none
        "
        style={{
          left: `${20 + password.length * 12}px`,
        }}
      >
        |
      </span>
    )}
  </div>

</div>

      <p className="text-red-500 font-bold mt-4">
        {isLocked
          ? `로그인 차단 중입니다. 남은 시간 ${remainingSeconds}초` 
          : error}
      </p>

      {(activeInput === "phone" ||
        activeInput === "password") && (

        <NumberKeyboard
          onInput={(value) => {

            if (activeInput === "phone") {

              if (value === "BACK") {

                setPhone(phone.slice(0, -1));

                return;
              }

              if (phone.length < 11) {

                setPhone(phone + value);
              }
            }

            if (activeInput === "password") {

              if (value === "BACK") {

                setPassword(password.slice(0, -1));

                return;
              }

              if (password.length < 6) {

                setPassword(password + value);
              }
            }
          }}
        />

      )}

      <div className="flex gap-6 mt-8">

        <button
          onClick={login}
          disabled={
            isLocked ||
            phone.length !== 11 ||
            password.length !== 6
          }
          className={`
            w-[180px]
            h-[60px]
            rounded-2xl
            text-2xl
            font-bold
            transition

            ${
              !isLocked &&
              phone.length === 11 &&
              password.length === 6
                ? "bg-[#213555] text-white"
                : "bg-gray-400 text-gray-200"
            }
          `}
        >
          확인
        </button>

        <button
          onClick={() => navigate("/")}
          className="
            w-[180px]
            h-[60px]
            rounded-2xl
            bg-[#213555]
            text-white
            text-2xl
            font-bold
          "
        >
          홈
        </button>

      </div>

    </div>
  );
}