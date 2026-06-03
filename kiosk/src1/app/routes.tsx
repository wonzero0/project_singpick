import { createBrowserRouter } from "react-router-dom";

// Screens
import KioskHome from "./screens/KioskHome";
import Login from "./screens/Login";
import Signup from "./screens/Signup";
import SongSelect from "./screens/SongSelect";
import { MainReservation } from "./screens/MainReservation";
import { Session } from "./screens/Session";
import { Feedback } from "./screens/Feedback";

// External
import Web from "../../webpage_backup/src/Web/Web";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: KioskHome,
  },
  {
    path: "/login",
    Component: Login,
  },
  {
    path: "/signup",
    Component: Signup,
  },
  {
    path: "/song",
    Component: SongSelect,
  },
  {
    path: "/reservation",
    Component: MainReservation,
  },
  {
    path: "/session",
    Component: Session,
  },
  {
    path: "/feedback",
    Component: Feedback,
  },
  {
    path: "/web",
    element: <Web />,
  },
]);