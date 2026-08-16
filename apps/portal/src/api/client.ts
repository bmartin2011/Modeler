export async function getMilkyWay(lens: "value_stream" | "organization") {
  const response = await fetch(`/api/views/milky-way?lens=${lens}`);

  if (!response.ok) {
    throw new Error(`Modeler API request failed: ${response.status} ${response.statusText}`);
  }

  return response.json();
}
