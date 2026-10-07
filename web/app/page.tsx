import { Chat } from "@/components/chat";

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { q } = await searchParams;
  const initialQuestion = typeof q === "string" ? q.trim() : "";
  return <Chat initialQuestion={initialQuestion} />;
}
