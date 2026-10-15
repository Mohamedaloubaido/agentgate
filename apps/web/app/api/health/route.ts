export async function GET() {
  return Response.json({
    status: 'ok',
    service: 'agentgate-web',
    version: '0.1.0',
  });
}
