// Temporary fix - return 404 for NextAuth routes until we fix the handlers issue
export async function GET() {
  return new Response('NextAuth not configured', { status: 404 });
}

export async function POST() {
  return new Response('NextAuth not configured', { status: 404 });
}
