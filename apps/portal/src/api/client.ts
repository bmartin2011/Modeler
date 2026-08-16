export async function getMilkyWay(lens: "value_stream" | "organization") {
  const response = await fetch(`/api/views/milky-way?lens=${lens}`);
  return response.json();
}
