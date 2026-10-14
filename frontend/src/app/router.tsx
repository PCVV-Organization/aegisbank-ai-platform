import {
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  Link,
  redirect,
} from "@tanstack/react-router";
import { useAuth } from "../auth/use-auth";
import { AssistantPage } from "../features/assistant/assistant-page";
import { ServiceRequestForm } from "../features/service-requests/service-request-form";

function AppShell() {
  const { user, signOut } = useAuth();
  return (
    <>
      <a className="skip-link" href="#main-content">
        Skip to content
      </a>
      <div className="min-h-screen md:flex">
        <aside className="border-slate-200 bg-[#0f2747] p-4 text-white md:w-64">
          <div className="mb-8 text-xl font-semibold">AegisBank</div>
          <nav aria-label="Primary navigation" className="grid gap-1">
            {[
              "overview",
              "accounts",
              "cards",
              "loans",
              "payments",
              "service-requests",
              "assistant",
            ].map((item) => (
              <Link
                key={item}
                to={`/app/${item}` as never}
                className="rounded px-3 py-2 text-sm hover:bg-white/10 [&.active]:bg-white/15"
              >
                {item.replace("-", " ").replace(/^./, (c) => c.toUpperCase())}
              </Link>
            ))}
          </nav>
          <div className="mt-8 border-t border-white/20 pt-4 text-sm">
            <p className="mb-2 text-slate-300">
              {user?.name ?? "Synthetic customer"}
            </p>
            <button
              className="rounded border border-white/40 px-3 py-2"
              onClick={signOut}
            >
              Sign out
            </button>
          </div>
        </aside>
        <main id="main-content" className="min-w-0 flex-1 p-4 md:p-8">
          <Outlet />
        </main>
      </div>
    </>
  );
}

function LoginPage() {
  const { signIn } = useAuth();
  return (
    <main className="grid min-h-screen place-items-center p-6">
      <section className="w-full max-w-md rounded-xl bg-white p-8 shadow-sm">
        <h1 className="mb-2 text-2xl font-semibold">Welcome to AegisBank</h1>
        <p className="mb-6 text-slate-600">
          Synthetic banking laboratory portal.
        </p>
        <button
          className="w-full rounded-lg bg-[#0f2747] px-4 py-3 font-medium text-white"
          onClick={signIn}
        >
          Sign in
        </button>
      </section>
    </main>
  );
}

function Page({
  title,
  children,
}: {
  title: string;
  children?: React.ReactNode;
}) {
  return (
    <section>
      <h1 className="mb-2 text-3xl font-semibold text-[#0f2747]">{title}</h1>
      {children ?? (
        <p className="text-slate-600">
          This module is ready for its next domain slice.
        </p>
      )}
    </section>
  );
}

const rootRoute = createRootRoute({ component: () => <Outlet /> });
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/login",
  component: LoginPage,
});
const appRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/app",
  beforeLoad: () => {
    if (!useAuth.getState().user) throw redirect({ to: "/login" });
  },
  component: AppShell,
});
const overviewRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/overview",
  component: () => (
    <Page title="Overview">
      <div className="mt-6 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Available balance</p>
          <p className="mt-2 text-2xl font-semibold">$12,480.00</p>
        </article>
        <article className="rounded-xl bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Open requests</p>
          <p className="mt-2 text-2xl font-semibold">2</p>
        </article>
        <article className="rounded-xl bg-white p-5 shadow-sm">
          <p className="text-sm text-slate-500">Assistant</p>
          <Link
            className="mt-2 inline-block text-blue-700 underline"
            to="/app/assistant"
          >
            Ask Aegis
          </Link>
        </article>
      </div>
    </Page>
  ),
});
const assistantRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/assistant",
  component: AssistantPage,
});
const placeholderRoutes = ["accounts", "cards", "loans", "payments"].map(
  (path) =>
    createRoute({
      getParentRoute: () => appRoute,
      path: `/${path}`,
      component: () => (
        <Page
          title={path.replace("-", " ").replace(/^./, (c) => c.toUpperCase())}
        />
      ),
    }),
);
const serviceRequestsRoute = createRoute({
  getParentRoute: () => appRoute,
  path: "/service-requests",
  component: () => (
    <Page title="Service requests">
      <ServiceRequestForm />
    </Page>
  ),
});
const routeTree = rootRoute.addChildren([
  loginRoute,
  appRoute.addChildren([
    overviewRoute,
    assistantRoute,
    serviceRequestsRoute,
    ...placeholderRoutes,
  ]),
]);
export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
