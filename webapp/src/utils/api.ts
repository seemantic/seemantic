export const fetchApi = async <T>(route: string): Promise<T> => {
    const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/${route}`);
    if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status} - ${response.statusText}`);
    }
    return (await response.json()) as T;
};