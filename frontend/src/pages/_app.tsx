import "@/styles/globals.css";
import type { AppProps } from "next/app";
import { useEffect } from "react";
import { useRouter } from "next/router";
import { pageview } from "@/lib/gtag";
import GoogleAnalytics from "@/components/GoogleAnalytics";

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();

  useEffect(() => {
    // Track page views on route changes
    const handleRouteChange = (url: string) => {
      pageview(url);
    };

    router.events.on("routeChangeComplete", handleRouteChange);
    
    // Track initial page load
    pageview(router.asPath);

    return () => {
      router.events.off("routeChangeComplete", handleRouteChange);
    };
  }, [router.events, router.asPath]);

  return (
    <>
      <GoogleAnalytics />
      <Component {...pageProps} />
    </>
  );
}
