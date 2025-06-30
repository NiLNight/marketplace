// src/components/ReviewList.tsx
import {useInfiniteQuery} from '@tanstack/react-query';
import apiClient from '../api';
import {ReviewCard, type Review} from './ReviewCard';

interface ApiResponse {
    results: Review[];
    next: string | null;
}

const fetchReviews = async ({pageParam = 1, productId}: {
    pageParam?: number;
    productId: number
}): Promise<ApiResponse> => {
    const {data} = await apiClient.get<ApiResponse>(`/reviews/${productId}/`, {params: {page: pageParam}});
    return data;
};

export function ReviewList({productId}: { productId: number }) {
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isLoading,
        isFetchingNextPage
    } = useInfiniteQuery({
        queryKey: ['reviews', productId],
        queryFn: ({pageParam}) => fetchReviews({pageParam, productId}),
        getNextPageParam: (lastPage) => {
            if (lastPage.next) {
                try {
                    const url = new URL(lastPage.next);
                    return Number(url.searchParams.get('page'));
                } catch {
                    return undefined;
                }
            }
            return undefined;
        },
        initialPageParam: 1,
    });

    if (isLoading) {
        return <div className="text-center text-white">Загрузка отзывов...</div>;
    }

    const reviews = data?.pages.flatMap(page => page.results) ?? [];

    if (reviews.length === 0) {
        return <div className="text-center text-slate-400 p-8 bg-slate-800 rounded-lg">Отзывов пока нет. Будьте
            первым!</div>
    }

    return (
        <div className="space-y-4">
            {reviews.map(review => <ReviewCard key={review.id} review={review} productId={productId}/>)}
            {hasNextPage && (
                <div className="text-center">
                    <button onClick={() => fetchNextPage()} disabled={isFetchingNextPage}
                            className="rounded-md bg-slate-700 px-4 py-2 text-white hover:bg-slate-600">
                        {isFetchingNextPage ? 'Загрузка...' : 'Показать еще'}
                    </button>
                </div>
            )}
        </div>
    );
}