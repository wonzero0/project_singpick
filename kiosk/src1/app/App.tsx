import { RouterProvider } from "react-router-dom";
import { router } from "./routes";
import { useEffect } from "react";

export default function App() {

  useEffect(() => {

    // 🤍 앱 시작 시 흰 조명
    fetch("http://127.0.0.1:8000/led/stop", {
      method: "POST",
    });

  }, []);

  return <RouterProvider router={router} />;
}