import { RedefinirSenhaClient } from "./redefinir-senha-client";

export default async function RedefinirSenhaPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <RedefinirSenhaClient token={token} />;
}
