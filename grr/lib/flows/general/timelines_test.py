#!/usr/bin/env python
# -*- mode: python; encoding: utf-8 -*-
"""Tests for the Timelines flow."""

from grr.client.client_actions import standard
from grr.lib import action_mocks
from grr.lib import aff4
from grr.lib import flags
from grr.lib import flow_runner
from grr.lib import test_lib
# pylint: disable=unused-import
from grr.lib.flows.general import timelines as _
# pylint: enable=unused-import
from grr.lib.rdfvalues import paths as rdf_paths


class TestTimelines(test_lib.FlowTestsBaseclass):
  """Test the timelines flow."""

  client_id = "C.0000000000000005"

  def testMACTimes(self):
    """Test that the timelining works with files."""
    with test_lib.VFSOverrider(rdf_paths.PathSpec.PathType.OS,
                               test_lib.ClientVFSHandlerFixture):

      client_mock = action_mocks.ActionMock(standard.ListDirectory)

      pathspec = rdf_paths.PathSpec(
          path="/", pathtype=rdf_paths.PathSpec.PathType.OS)

      for _ in test_lib.TestFlowHelper(
          "RecursiveListDirectory",
          client_mock,
          client_id=self.client_id,
          pathspec=pathspec,
          token=self.token):
        pass

      # Now make a timeline
      for s in test_lib.TestFlowHelper(
          "MACTimes",
          client_mock,
          client_id=self.client_id,
          token=self.token,
          path="/"):
        session_id = s

      fd = aff4.FACTORY.Open(
          session_id.Add(flow_runner.RESULTS_SUFFIX), token=self.token)

      timestamp = 0
      events = list(fd.Query("event.stat.pathspec.path contains grep"))

      for event in events:
        # Check the times are monotonously increasing.
        self.assertGreaterEqual(event.event.timestamp, timestamp)
        timestamp = event.event.timestamp

        self.assertIn("grep", event.event.stat.pathspec.path)

      # 9 files, each having mac times = 27 events.
      self.assertEqual(len(events), 27)


def main(argv):
  # Run the full test suite
  test_lib.GrrTestProgram(argv=argv)


if __name__ == "__main__":
  flags.StartMain(main)
