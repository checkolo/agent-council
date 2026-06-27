import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppShell } from "@/components/shell/AppShell";
import { Dashboard } from "@/pages/Dashboard";
import { NewRun } from "@/pages/NewRun";
import { RunView } from "@/pages/RunView";
import { CassetteView } from "@/pages/CassetteView";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <Dashboard /> },
      { path: "new", element: <NewRun /> },
      { path: "runs/:id", element: <RunView /> },
      { path: "cassette", element: <CassetteView /> },
    ],
  },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
