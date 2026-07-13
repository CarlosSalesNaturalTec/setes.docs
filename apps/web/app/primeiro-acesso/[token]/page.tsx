import { PrimeiroAcessoClient } from "./primeiro-acesso-client";

export default async function PrimeiroAcessoPage({
  params,
}: {
  params: Promise<{ token: string }>;
}) {
  const { token } = await params;
  return <PrimeiroAcessoClient token={token} />;
}
