export default function SessionPage({ params }: { params: { id: string } }) {
  return (
    <div className="flex h-screen w-screen items-center justify-center bg-black text-white">
      <div className="text-center">
        <h1 className="text-3xl font-bold mb-2">Live Session</h1>
        <p className="text-gray-400">Session ID: {params.id}</p>
        <div className="mt-8 p-4 border border-gray-700 rounded-lg">
          <p>Video/Audio Interface will be rendered here (Epic 26)</p>
        </div>
      </div>
    </div>
  );
}
