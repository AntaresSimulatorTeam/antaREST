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

import { insertFoldersIfNotExist, insertWorkspacesIfNotExist } from "../utils";
import { NonStudyFolderDTO, StudyTreeNode } from "../../utils";
import { FIXTURES } from "./fixtures";

describe("StudyTree Utils", () => {
  describe("mergeStudyTreeAndFolders", () => {
    test.each(Object.values(FIXTURES))(
      "$name",
      ({ studyTree, folders, expected }) => {
        const result = insertFoldersIfNotExist(studyTree, folders);
        expect(result).toEqual(expected);
      },
    );

    test("should handle empty study tree", () => {
      const emptyTree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [],
      };
      const result = insertFoldersIfNotExist(emptyTree, []);
      expect(result).toEqual(emptyTree);
    });

    test("should handle empty folders array", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [{ name: "a", path: "/a", children: [] }],
      };
      const result = insertFoldersIfNotExist(tree, []);
      expect(result).toEqual(tree);
    });

    test("should handle invalid parent paths", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [{ name: "a", path: "/a", children: [] }],
      };
      const invalidFolder: NonStudyFolderDTO = {
        name: "invalid",
        path: "/invalid",
        workspace: "nonexistent",
        parentPath: "/nonexistent",
      };
      const result = insertFoldersIfNotExist(tree, [invalidFolder]);
      expect(result).toEqual(tree);
    });

    test("should handle empty workspaces", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [
          {
            name: "a",
            path: "/a",
            children: [{ name: "suba", path: "/a/suba", children: [] }],
          },
        ],
      };
      const workspaces: string[] = [];
      const result = insertWorkspacesIfNotExist(tree, workspaces);
      expect(result).toEqual(tree);
    });

    test("should merge workspaces", () => {
      const tree: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [
          {
            name: "a",
            path: "/a",
            children: [{ name: "suba", path: "/a/suba", children: [] }],
          },
        ],
      };
      const expected: StudyTreeNode = {
        name: "Root",
        path: "/",
        children: [
          {
            name: "a",
            path: "/a",
            children: [{ name: "suba", path: "/a/suba", children: [] }],
          },
          { name: "workspace1", path: "/workspace1", children: [] },
          { name: "workspace2", path: "/workspace2", children: [] },
        ],
      };

      const workspaces: string[] = ["a", "workspace1", "workspace2"];
      const result = insertWorkspacesIfNotExist(tree, workspaces);
      expect(result).toEqual(expected);
    });
  });
});
