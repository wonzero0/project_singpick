import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import NumberKeyboard from "../components/NumberKeyboard";
import EnglishKeyboard from "../components/EnglishKeyboard";

export default function Signup() {

  const navigate = useNavigate();

  const [userId, setUserId] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");

  const [error, setError] = useState("");

  const [activeInput, setActiveInput] = useState<
    "id" | "phone" | "password" | null
  >(null);

  useEffect(() => {
    fetch("/kiosk/led", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ color: "GREEN" }),
    }).catch(() => {
      console.warn("외부 LED GREEN 명령 전송 실패");
    });
  }, []);

  const signup = async () => {

    try {

      const res = await fetch(
        "/users/signup",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            user_id: userId,
            phone,
            password,
          }),
        }
      );

      if (res.ok) {
        navigate("/");
      } else {
        const data = await res.json();
        setError(
          typeof data.detail === "string"
            ? data.detail
            : "회원가입 실패"
        );
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
      gap-1
      items-center
      justify-center
    ">

      <h1 className="text-5xl font-bold mb-3">
        회원가입
      </h1>

      <div className="relative">
        <input
          value={userId}
          readOnly
          placeholder="아이디 입력 (4자 이상)"
          onClick={() => setActiveInput("id")}
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
              activeInput === "id"
                ? "border-[#213555]"
                : "border-[#AAB7C4]"
            }
          `}
        />

        {activeInput === "id" && (
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
        left: `${20 + userId.length * 12}px`,
      }}
    >
      |
    </span>
  )}
</div>

        <div className="relative">
  <input
    type="tel"
    value={phone}
    readOnly
    placeholder="전화번호 입력 (010 포함)"
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
    placeholder="비밀번호 입력 (숫자 6개)"
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

      <p className="text-red-500 font-bold mt-4">
        {error}
      </p>

      {activeInput === "id" && (

        <EnglishKeyboard
          onInput={(value) => {

            if (value === "BACK") {

              setUserId(userId.slice(0, -1));

              return;
            }

            setUserId(userId + value);
          }}
        />

      )}

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
          onClick={signup}
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
          등록
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