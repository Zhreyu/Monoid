'use client';

import { useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';

export default function SPARedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const redirectPath = searchParams.get('p');
    if (redirectPath) {
      // Remove the ?p= param and navigate to the actual path
      router.replace(redirectPath);
    }
  }, [router, searchParams]);

  return null;
}
