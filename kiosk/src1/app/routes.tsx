import { createBrowserRouter } from "react-router";
import { MainReservation } from "./screens/MainReservation";
import { Session } from "./screens/Session";
import { Feedback } from "./screens/Feedback";

import Web from "../../webpage_backup/src/Web/Web";

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
  {
    path: "/web",
    element: <Web />,
  },
]);