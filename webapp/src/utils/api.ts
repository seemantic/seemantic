export const fetchApi = async <T>(route: string): Promise<T> => {
    const url = `${process.env.NEXT_PUBLIC_API_URL}/api/v1/${route}`
    const response = await fetch(url);
    if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status} - ${response.statusText}`);
    }
    return (await response.json()) as T;
};


export interface ApiDocumentSnippet {
    uri: string; // Relative path within the source
    status: "pending" | "indexing" | "indexing_success" | "indexing_error"; // Status of the document
    error_status_message?: string | null; // Optional error message
    last_indexing?: string | null; // ISO 8601 string for the last indexing timestamp
}

export interface ApiExplorer {
    documents: ApiDocumentSnippet[]; // List of ApiDocumentSnippet objects
}


export const get_explorer = (): Promise<ApiExplorer> => fetchApi<ApiExplorer>("explorer")