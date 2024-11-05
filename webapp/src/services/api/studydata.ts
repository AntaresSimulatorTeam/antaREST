/**
 * Copyright (c) 2024, RTE (https://www.rte-france.com)
 *
 * See AUTHORS.txt
 *
 * This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/.
 *
 * SPDX-License-Identifier: MPL-2.0
 *
 * This file is part of the Antares project.
 */

import {
  LinkCreationInfoDTO,
  LinkInfoWithUI,
  UpdateAreaUi,
} from "@/common/types";
import {
  BindingConstraint,
  bindingConstraintModelAdapter,
  ConstraintTerm,
} from "@/components/App/Singlestudy/explore/Modelization/BindingConstraints/BindingConstView/utils";
import { StudyMapNode } from "@/redux/ducks/studyMaps";

import client from "./client";

export const createArea = async (
  uuid: string,
  name: string,
): Promise<StudyMapNode> => {
  const res = await client.post(`/v1/studies/${uuid}/areas`, {
    name,
    type: "AREA",
  });
  return res.data;
};

export const createLink = async (
  uuid: string,
  linkCreationInfo: LinkCreationInfoDTO,
): Promise<string> => {
  const res = await client.post(`/v1/studies/${uuid}/links`, linkCreationInfo);
  return res.data;
};

export const updateAreaUI = async (
  uuid: string,
  areaId: string,
  layerId: string,
  areaUi: UpdateAreaUi,
): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${uuid}/areas/${areaId}/ui?layer=${layerId}`,
    areaUi,
  );
  return res.data;
};

export const deleteArea = async (
  uuid: string,
  areaId: string,
): Promise<string> => {
  const res = await client.delete(`/v1/studies/${uuid}/areas/${areaId}`);
  return res.data;
};

export const deleteLink = async (
  uuid: string,
  areaIdFrom: string,
  areaIdTo: string,
): Promise<string> => {
  const res = await client.delete(
    `/v1/studies/${uuid}/links/${areaIdFrom}/${areaIdTo}`,
  );
  return res.data;
};

export const updateConstraintTerm = async (
  studyId: string,
  constraintId: string,
  term: Partial<ConstraintTerm>,
): Promise<string> => {
  const res = await client.put(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}/term`,
    term,
  );
  return res.data;
};

export const createConstraintTerm = async (
  studyId: string,
  constraintId: string,
  term: ConstraintTerm,
): Promise<void> => {
  const res = await client.post(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}/term`,
    term,
  );
  return res.data;
};

export const deleteConstraintTerm = async (
  studyId: string,
  constraintId: string,
  termId: ConstraintTerm["id"],
): Promise<void> => {
  const res = await client.delete(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}/term/${encodeURIComponent(termId)}`,
  );
  return res.data;
};

export const getBindingConstraint = async (
  studyId: string,
  constraintId: string,
): Promise<BindingConstraint> => {
  const res = await client.get(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}`,
  );

  return bindingConstraintModelAdapter(res.data);
};

export const getBindingConstraintList = async (
  studyId: string,
): Promise<BindingConstraint[]> => {
  const res = await client.get(`/v1/studies/${studyId}/bindingconstraints`);
  return res.data;
};

export const updateBindingConstraint = async (
  studyId: string,
  constraintId: string,
  data: Omit<BindingConstraint, "id" | "name">,
): Promise<void> => {
  const adaptedData = bindingConstraintModelAdapter(data as BindingConstraint); // TODO fix type

  const res = await client.put(
    `/v1/studies/${studyId}/bindingconstraints/${encodeURIComponent(
      constraintId,
    )}`,
    adaptedData,
  );
  return res.data;
};

export const createBindingConstraint = async (
  studyId: string,
  data: Partial<BindingConstraint>,
): Promise<BindingConstraint> => {
  const res = await client.post(
    `/v1/studies/${studyId}/bindingconstraints`,
    data,
  );
  return res.data;
};

interface GetAllLinksParams {
  uuid: string;
  withUi?: boolean;
}

type LinkTypeFromParams<T extends GetAllLinksParams> = T["withUi"] extends true
  ? LinkInfoWithUI
  : LinkCreationInfoDTO;

export const getAllLinks = async <T extends GetAllLinksParams>(
  params: T,
): Promise<Array<LinkTypeFromParams<T>>> => {
  const { uuid, withUi } = params;
  const withUiStr = withUi ? "with_ui=true" : "";
  const res = await client.get(`/v1/studies/${uuid}/links?${withUiStr}`);
  return res.data;
};
