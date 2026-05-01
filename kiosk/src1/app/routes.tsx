import { createBrowserRouter } from "react-router";
import { MainReservation } from "./screens/MainReservation";
import { Session } from "./screens/Session";
import { Feedback } from "./screens/Feedback";

export const router = createBrowserRouter([
  {
    path: "/",
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
]);
