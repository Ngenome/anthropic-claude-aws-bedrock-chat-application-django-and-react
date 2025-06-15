import React from "react";
import { useParams, useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Layout } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

import { fetchGroup, fetchGroupPrototypes } from "@/services/prototypes";

const PrototypesByGroup: React.FC = () => {
  const { groupId } = useParams<{ groupId: string }>();
  const navigate = useNavigate();

  // Fetch group details
  const {
    data: group,
    isLoading: isGroupLoading,
    isError: isGroupError,
  } = useQuery({
    queryKey: ["group", groupId],
    queryFn: () => fetchGroup(Number(groupId)),
    enabled: !!groupId,
  });

  // Fetch group prototypes
  const {
    data: prototypes,
    isLoading: isPrototypesLoading,
    isError: isPrototypesError,
  } = useQuery({
    queryKey: ["groupPrototypes", groupId],
    queryFn: () => fetchGroupPrototypes(Number(groupId)),
    enabled: !!groupId,
  });

  if (isGroupError || isPrototypesError) {
    return (
      <div className="container mx-auto p-4">
        <div className="text-center text-red-500">
          Error loading group data. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex items-center mb-6">
        <Button variant="ghost" onClick={() => navigate(-1)} className="mr-4">
          <ArrowLeft className="h-4 w-4 mr-2" />
          Back
        </Button>
        {isGroupLoading ? (
          <Skeleton className="h-8 w-64" />
        ) : (
          <h1 className="text-2xl font-bold">{group?.name}</h1>
        )}
      </div>

      <div className="mb-6">
        {isGroupLoading ? (
          <Skeleton className="h-20 w-full" />
        ) : (
          <p className="text-muted-foreground">{group?.description}</p>
        )}
      </div>

      <div className="mb-6">
        <h2 className="text-xl font-semibold mb-4">Prototypes in this Group</h2>

        {isPrototypesLoading ? (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {[1, 2, 3].map((n) => (
              <Card key={n} className="overflow-hidden">
                <CardHeader>
                  <Skeleton className="h-5 w-1/2 mb-2" />
                </CardHeader>
                <CardContent>
                  <Skeleton className="h-40 w-full" />
                </CardContent>
                <CardFooter className="flex justify-end">
                  <Skeleton className="h-9 w-24" />
                </CardFooter>
              </Card>
            ))}
          </div>
        ) : prototypes?.length === 0 ? (
          <div className="text-center py-10">
            <Layout className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
            <p className="text-lg text-muted-foreground mb-4">
              No prototypes in this group
            </p>
            <p className="text-muted-foreground mb-6">
              Go to a design project to generate new prototypes for this group.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {prototypes?.map((prototype) => (
              <Card key={prototype.id} className="overflow-hidden">
                <CardHeader>
                  <CardTitle className="text-lg">{prototype.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="aspect-video bg-muted rounded-md flex items-center justify-center">
                    <Layout className="h-8 w-8 text-muted-foreground" />
                  </div>
                  <p className="text-sm text-muted-foreground mt-2 line-clamp-2">
                    {prototype.description}
                  </p>
                </CardContent>
                <CardFooter className="flex justify-end">
                  <Button
                    variant="default"
                    onClick={() => navigate(`/prototypes/${prototype.id}`)}
                  >
                    View Prototype
                  </Button>
                </CardFooter>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PrototypesByGroup;
