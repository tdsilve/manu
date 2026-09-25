import type { Metadata } from "next";
import { Chat } from "@/components/chat";

export const metadata: Metadata = { title: "Chat · Manu" };

export default async function ChatPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { q } = await searchParams;
  const initialQuestion = typeof q === "string" ? q.trim() : "";
  return <Chat initialQuestion={initialQuestion} />;
}
