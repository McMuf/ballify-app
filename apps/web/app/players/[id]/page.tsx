import PlayerDetailClient from "./PlayerDetailClient";

export default async function PlayerDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <PlayerDetailClient playerId={Number(id)} />;
}
