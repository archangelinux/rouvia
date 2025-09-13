import { NextResponse } from 'next/server';

export async function POST(req: Request) {
  const body = await req.json();  // your ChatMessage object
  console.log('Received message:', body);

  // Temporary response so you can see it works
  return NextResponse.json({ status: 'ok', received: body });
}