import { createBrowserRouter } from "react-router-dom";

import KioskHome from "./screens/KioskHome";
import Login from "./screens/Login";
import Signup from "./screens/Signup";
import SongSelect from "./screens/SongSelect";

import { MainReservation } from "./screens/MainReservation";
import { Session } from "./screens/Session";
import { Feedback } from "./screens/Feedback";

export const router = createBrowserRouter([

  // 🔥 키오스크 첫 화면
  {
    path: "/",
    Component: KioskHome,
  },

  // 로그인
  {
    path: "/login",
    Component: Login,
  },

  // 회원가입
  {
    path: "/signup",
    Component: Signup,
  },

  // 곡 수 선택
  {
    path: "/song",
    Component: SongSelect,
  },

  // 🔥 내부 예약 화면
  {
    path: "/reservation",
    Component: MainReservation,
  },

  // 노래 세션 화면
  {
    path: "/session",
    Component: Session,
  },

  // 피드백 화면
  {
    path: "/feedback",
    Component: Feedback,
  },

]);
