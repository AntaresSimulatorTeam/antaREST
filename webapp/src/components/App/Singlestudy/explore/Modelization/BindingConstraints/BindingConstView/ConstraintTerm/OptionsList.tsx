import { useMemo } from "react";
import { useTranslation } from "react-i18next";
import { AllClustersAndLinks } from "../../../../../../../../common/types";
import SelectSingle from "../../../../../../../common/SelectSingle";
import { ConstraintTerm, generateTermId, isTermExist } from "../utils";

interface Option {
  id: string;
  name: string;
}
interface Props {
  list: AllClustersAndLinks;
  isLink: boolean;
  term: ConstraintTerm;
  constraintTerms: ConstraintTerm[];
  saveValue: (term: ConstraintTerm) => void;
  selectedArea: string;
  selectedClusterOrArea: string;
  setSelectedArea: (value: string) => void;
  setSelectedClusterOrArea: (value: string) => void;
}

export default function OptionsList({
  list,
  isLink,
  term,
  constraintTerms,
  saveValue,
  selectedArea,
  selectedClusterOrArea,
  setSelectedArea,
  setSelectedClusterOrArea,
}: Props) {
  const [t] = useTranslation();

  const areaOptions = useMemo(
    () =>
      list.links.map(({ element }) => ({
        name: element.name,
        id: element.id,
      })),
    [list.links],
  );

  const clusterOrAreaOptions = useMemo(() => {
    if (!selectedArea) {
      return [];
    }

    // Determine the type of options to use based on whether it is a link or cluster
    const relatedOptions = isLink ? list.links : list.clusters;

    // Attempt to find the option that matches the selected area
    const foundOption = relatedOptions.find(
      ({ element }) => element.id === selectedArea,
    );

    if (!foundOption) {
      return [];
    }

    return foundOption.item_list.reduce<Option[]>((acc, { id, name }) => {
      const termId = generateTermId(
        isLink
          ? { area1: selectedArea, area2: id }
          : { area: selectedArea, cluster: id },
      );

      // Check if the id is valid
      if (
        id === selectedClusterOrArea ||
        !isTermExist(constraintTerms, termId)
      ) {
        acc.push({ name, id: id.toLowerCase() });
      }

      return acc;
    }, []);
  }, [
    selectedArea,
    isLink,
    list.links,
    list.clusters,
    selectedClusterOrArea,
    constraintTerms,
  ]);

  ////////////////////////////////////////////////////////////////
  // Event Handlers
  ////////////////////////////////////////////////////////////////

  const handleAreaChange = (value: string) => {
    setSelectedArea(value);
  };

  const handleClusterOrAreaChange = (value: string) => {
    setSelectedClusterOrArea(value);
    saveValue({
      ...term,
      data: isLink
        ? { area1: selectedArea, area2: value }
        : { area: selectedArea, cluster: value },
    });
  };

  ////////////////////////////////////////////////////////////////
  // JSX
  ////////////////////////////////////////////////////////////////

  return (
    <>
      <SelectSingle
        disabled
        size="small"
        variant="outlined"
        name="selectedArea"
        label={t(`study.${isLink ? "area1" : "area"}`)}
        data={selectedArea}
        list={areaOptions}
        handleChange={(key, value) => handleAreaChange(value as string)}
        sx={{
          maxWidth: 200,
          mr: 1,
        }}
      />
      <SelectSingle
        size="small"
        variant="outlined"
        name="selectedClusterOrArea"
        label={t(`study.${isLink ? "area2" : "cluster"}`)}
        data={selectedClusterOrArea.toLowerCase()}
        list={clusterOrAreaOptions}
        handleChange={(key, value) =>
          handleClusterOrAreaChange(value as string)
        }
        sx={{
          maxWidth: 200,
        }}
      />
    </>
  );
}
